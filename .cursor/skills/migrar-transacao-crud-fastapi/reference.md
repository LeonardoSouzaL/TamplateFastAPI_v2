# Referência — migração de transação CRUD

Complementa [SKILL.md](SKILL.md). Rules: `015-db-session-auto.mdc`, `040-crud-auto.mdc`, `045-crud-transaction-commit-auto.mdc`. Template de sessão: `docs/cursor/templates/db/session.py`.

## Padrões de varredura (rg)

Execute na raiz do projeto. Ajuste pastas se a estrutura divergir.

```bash
# Commits explícitos (service/endpoint)
rg -n "\.commit\(" api/ services/ crud/ db/

# Flush / rollback
rg -n "\.flush\(|\.rollback\(" api/ services/ crud/

# commit=False já em uso
rg -n "commit\s*=\s*False" api/ services/ crud/

# get_db com possível auto-commit
rg -n "async def get_db|def get_db" db/ api/
rg -n "commit\(|rollback\(" db/session.py db/session.py

# Writes CRUD comuns
rg -n "\.create\(|\.update\(|\.remove\(" api/ services/

# Loop + persistência
rg -n "for .+ in .+:" -A 8 api/ services/ | rg -n "commit\(|\.create\(|\.update\(|\.remove\("

# BackgroundTasks + sessão
rg -n "BackgroundTasks|background" api/ services/
rg -n "AsyncSession|get_db|Depends\(get_db\)|DbDep" api/ services/ --glob "*task*"

# refresh após carga
rg -n "\.refresh\(" api/ services/ crud/
```

Priorizar leitura manual de funções com **2+** chamadas `create`/`update`/`remove` na mesma sessão.

## Checklist baseline (Fase 0)

- [ ] `crud/base.py` (ou equivalente): `create`/`update`/`remove` aceitam `commit: bool = True`
- [ ] `commit=True` → `commit()` + `refresh()` quando necessário
- [ ] `commit=False` → `flush()` (+ `refresh()` se precisar de id gerado)
- [ ] `db/session.py`: `async_sessionmaker(..., expire_on_commit=False)`
- [ ] `get_db` **sem** auto-commit no happy path
- [ ] `api/deps.py`: alias `DbDep` e endpoints usando-o

## Template `docs/crud-transaction-migration/inventario.md`

```markdown
# Inventário — transações CRUD

Gerado em: YYYY-MM-DD
Projeto: {nome}

| ID | Severidade | Arquivo | Função | Problema | Writes | Já commit=False? | Esforço |
|----|------------|---------|--------|----------|--------|------------------|---------|
| T-001 | Alta | services/order_service.py | finalize_order | 2 writes, 2 commits implícitos | create+update | Não | M |
| T-002 | Média | services/bulk_service.py | import_rows | commit em loop | N creates | Não | L |
| T-003 | Baixa | services/item_service.py | get_and_touch | refresh redundante | update | — | S |

## Legenda de severidade

- **Alta**: multi-write sem atomicidade; risco de inconsistência
- **Média**: N commits/request ou commit em loop (performance/pool)
- **Baixa**: higiene (refresh desnecessário, commit duplicado inofensivo)

## Gaps de baseline

- [ ] (listar se CRUD base / get_db não atendem Fase 0)
```

## Template `docs/crud-transaction-migration/plano-migracao.md`

```markdown
# Plano de migração — transação única por request

Gerado em: YYYY-MM-DD
Rules: 015, 040, 045
Skill: migrar-transacao-crud-fastapi

## Resumo executivo

- Ocorrências: Alta N / Média N / Baixa N
- Baseline OK: sim/não
- Riscos principais: ...
- Ganhos de performance esperados: menos round-trips; menor pressão no pool

## Ordem das fases

1. **Fase 0 — Baseline** (pré-requisito)
2. **Fase A — Alta severidade** (consistência)
3. **Fase B — Média severidade** (performance)
4. **Fase C — Baixa severidade** (higiene)

## Itens

### Fase 0 — Baseline

| Tarefa | Arquivo | Estado | Notas |
|--------|---------|--------|-------|
| commit: bool no CRUD base | crud/base.py | pendente/ok | default True |

### Fase A — Alta

| ID | Arquivo | Função | Problema | Padrão alvo | Testes | Esforço |
|----|---------|--------|----------|-------------|--------|---------|
| T-001 | ... | ... | ... | commit=False + commit único no service | commit 1x; rollback em falha | M |

### Fase B — Média

...

### Fase C — Baixa

...

## Checklist pós-fase

- [ ] Testes do módulo afetado passam
- [ ] Inventário atualizado (`status`)
- [ ] Sem `commit=False` órfão (sem commit no caller)
- [ ] BackgroundTasks com sessão própria
```

## Template `docs/crud-transaction-migration/status.md`

```markdown
# Status — migração de transação CRUD

| Fase | Itens | Feitos | Estado |
|------|-------|--------|--------|
| 0 Baseline | N | N | pendente/em_andamento/concluída |
| A Alta | N | N | ... |
| B Média | N | N | ... |
| C Baixa | N | N | ... |

## Log

| Data | Fase | Item | Ação | Resultado |
|------|------|------|------|-----------|
| YYYY-MM-DD | A | T-001 | MODO_APLICAR | testes OK |
```

## Exemplos de classificação

### Alta — multi-write sem atomicidade

```python
# ANTES (2 commits implícitos no CRUD)
history = await crud_history.create(db, obj_in=data)
await crud_order.update(db, db_obj=order, obj_in=update_data)

# DEPOIS
try:
    history = await crud_history.create(db, obj_in=data, commit=False)
    await crud_order.update(db, db_obj=order, obj_in=update_data, commit=False)
    await db.commit()
except Exception:
    await db.rollback()
    raise
```

### Média — commit em loop

```python
# ANTES
for row in rows:
    await crud_item.create(db, obj_in=row)  # N commits

# DEPOIS
try:
    for row in rows:
        await crud_item.create(db, obj_in=row, commit=False)
    await db.commit()
except Exception:
    await db.rollback()
    raise
```

Atenção: lote muito grande → considerar batch/chunk com commits controlados (performance vs memória), documentar no plano.

### Baixa — refresh redundante

```python
# ANTES
obj = await crud_item.get(db, id=item_id)
await db.refresh(obj)  # desnecessário se acabou de carregar

# DEPOIS: remover refresh; com expire_on_commit=False atributos permanecem acessíveis após commit
```

### Alta — BackgroundTasks com sessão da request

```python
# ERRADO
async def endpoint(db: DbDep, background_tasks: BackgroundTasks):
    background_tasks.add_task(work, db)  # sessão pode estar fechada

# CERTO: abrir sessão nova no worker; commit=True local
async def work():
    async with async_session_maker() as db:
        await crud_x.create(db, obj_in=payload, commit=True)
```

## Checklist de testes

Por fluxo migrado (preferir service):

- [ ] Happy path: `db.commit` (ou spy) chamado **uma vez**
- [ ] Falha no 2º write: `rollback` chamado; nada persistido parcialmente
- [ ] Default `commit=True` em callers de write único permanece compatível
- [ ] Background task não recebe a sessão da request
- [ ] Não misturar auto-commit em `get_db` com commit no CRUD

Exemplo stub (AsyncMock):

```python
async def test_finalize_commits_once(mock_db, ...):
    await service.finalize(...)
    mock_db.commit.assert_awaited_once()

async def test_finalize_rolls_back_on_second_failure(mock_db, ...):
    # segundo CRUD raise
    with pytest.raises(...):
        await service.finalize(...)
    mock_db.rollback.assert_awaited()
```

## Padrão CRUD base (compatível)

```python
async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType, commit: bool = True) -> ModelType:
    db_obj = self.model(**obj_in.model_dump())
    db.add(db_obj)
    if commit:
        await db.commit()
        await db.refresh(db_obj)
    else:
        await db.flush()
        await db.refresh(db_obj)
    return db_obj
```

Mesma assinatura em `update` e `remove`. Sessão síncrona: mesma regra sem `await`.

## Performance — regras para o plano

1. Um `commit` por request em fluxos multi-write.
2. Evitar `refresh()` quando objeto já está na sessão e `expire_on_commit=False`.
3. Background/workers: sessão nova, transação curta, `commit=True`.
4. Não manter transação aberta durante HTTP externo longo — decidir commit antes/depois conforme atomicidade de negócio (documentar no item do plano).
5. Evitar misturar abordagem A (commit no CRUD/service) com B (auto-commit em `get_db`).

## Referências

- `.cursor/rules/015-db-session-auto.mdc`
- `.cursor/rules/040-crud-auto.mdc`
- `.cursor/rules/045-crud-transaction-commit-auto.mdc`
- `docs/cursor/templates/db/session.py`
- Skill `executar-tarefa-template-fastapi` (refatoração multi-arquivo em MODO_APLICAR)
