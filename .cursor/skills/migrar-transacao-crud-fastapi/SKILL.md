---
name: migrar-transacao-crud-fastapi
description: Audita transações CRUD em projetos FastAPI, gera plano de migração para commit único por request (rules 015/040/045) e aplica refatorações fase a fase com confirmação. Use ao refatorar legado com múltiplos commits, get_db com auto-commit misturado, BackgroundTasks com sessão da request ou ao pedir plano de migração de transações.
disable-model-invocation: true
---

# Migrar transação CRUD FastAPI

## Objetivo

Alinhar o projeto às rules `015-db-session-auto`, `040-crud-auto` e `045-crud-transaction-commit-auto`: **CRUD persiste**; **service/endpoint orquestra** a transação com um único `commit` por request em fluxos multi-write.

Ganhos: atomicidade, menos round-trips ao banco e menor pressão no pool de conexões.

## Quando usar

- Legado com vários `commit()` implícitos na mesma requisição
- `get_db` com auto-commit misturado ao commit no CRUD
- `BackgroundTasks`/workers reutilizando `AsyncSession` da request
- Pedido explícito de plano ou migração de transações / `commit=False`

## Modos

| Modo | Comportamento |
|------|----------------|
| `MODO_PLANO` (default) | Somente análise e docs em `docs/crud-transaction-migration/` |
| `MODO_APLICAR` | Uma fase do plano por vez, após resumo de impacto e confirmação explícita |

Não migrar o projeto inteiro de uma vez. Em `MODO_APLICAR`, se não houver plano, rode `MODO_PLANO` primeiro.

Responder em PT-BR. Não inventar ocorrências — marcar origem (`detectado_no_codigo` / `inferido` / `pendente_validacao`).

## Fluxo

1. Resolver modo (`MODO_PLANO` se omitido).
2. Fase 0 — Baseline.
3. Fase 1 — Varredura.
4. Fase 2 — Classificação.
5. Fase 3 — Plano + inventário + status.
6. Se `MODO_APLICAR`: confirmar fase → aplicar → testes → atualizar status.

Detalhes de grep, templates e exemplos: [reference.md](reference.md).

## Fase 0 — Baseline

Pré-requisitos **antes** de migrar callers:

| Verificação | Esperado |
|-------------|----------|
| `crud/base.py` | `create`/`update`/`remove` com `commit: bool = True` |
| CRUD `commit=True` | `commit()` + `refresh()` quando necessário |
| CRUD `commit=False` | `flush()` (+ `refresh` se id gerado) |
| `db/session.py` | `expire_on_commit=False`; `get_db` **sem** auto-commit |
| `api/deps.py` | `DbDep` nos endpoints |

Gap de baseline → primeira fase do plano (não migrar callers sem isso). Template: `docs/cursor/templates/db/session.py`.

## Fase 1 — Varredura

Pastas: `api/`, `services/`, `crud/`, `db/`. Padrões em [reference.md](reference.md).

Anti-padrões a inventariar:

- 2+ writes CRUD na mesma função sem `commit=False`
- Vários `await db.commit()` no mesmo fluxo
- `get_db` com commit/rollback (abordagem B misturada à A)
- `commit()` dentro de loop
- `refresh()` após `select`/`get` que acabou de carregar o objeto
- Background/task reutilizando sessão da request
- Service **e** endpoint fazendo `commit` na mesma sessão

## Fase 2 — Classificação

| Severidade | Critério | Exemplo |
|------------|----------|---------|
| Alta | Inconsistência (multi-write sem transação única) | create + update sem atomicidade |
| Média | Performance (N commits/request) | commit em loop |
| Baixa | Higiene | refresh desnecessário |

Ordem de prioridade no plano: Baseline → Alta → Média → Baixa.

## Fase 3 — Plano de migração

Gerar/atualizar:

```text
docs/crud-transaction-migration/plano-migracao.md
docs/crud-transaction-migration/inventario.md
docs/crud-transaction-migration/status.md
```

Templates completos em [reference.md](reference.md).

Cada item do plano deve incluir: arquivo, função, problema, padrão alvo, testes sugeridos, esforço (S/M/L).

Ao final de `MODO_PLANO`, apresentar resumo executivo ao usuário e perguntar se deseja `MODO_APLICAR` em alguma fase.

## Fase 4 — Aplicação (`MODO_APLICAR`)

1. Ler plano/status; escolher **uma** fase ou item confirmado pelo usuário.
2. Resumir impacto (arquivos, risco) e **aguardar confirmação**.
3. Refatorar seguindo Skill `executar-tarefa-template-fastapi` (camadas corretas).
4. Padrão alvo:

```python
try:
    await crud_a.create(db, obj_in=data, commit=False)
    await crud_b.update(db, db_obj=obj, obj_in=upd, commit=False)
    await db.commit()
except Exception:
    await db.rollback()
    raise
```

5. Preferir **service** como dono da transação quando houver regra de negócio. Endpoint só em orquestração simples.
6. Write único: manter `commit=True` (default) — não obrigar `commit=False`.
7. Rodar testes do módulo; atualizar inventário/status.
8. Parar e pedir próxima fase — não encadear fases sem nova confirmação.

### Baseline (se gap)

Adicionar `commit: bool = True` no CRUD base **sem** alterar callers existentes; remover auto-commit de `get_db` se misturado.

## Regras de performance

- 1 `commit` por request em fluxos multi-write
- Evitar `refresh` redundante com `expire_on_commit=False`
- Background: sessão nova, transação curta, `commit=True`
- Não manter transação aberta durante HTTP externo longo — documentar decisão de negócio no item do plano
- Não misturar auto-commit em `get_db` com commit no CRUD

## Não fazer

- `commit=False` sem `commit()` final no caller
- `commit()` em loop sem necessidade
- Reutilizar `AsyncSession` da request em `BackgroundTasks`
- Migrar tudo em um único turno sem confirmação
- Inventar hotspots não vistos no código

## Saída esperada

| Arquivo | Conteúdo |
|---------|----------|
| `plano-migracao.md` | Resumo, fases, itens, checklist |
| `inventario.md` | Tabela de ocorrências classificadas |
| `status.md` | Progresso (atualizado em `MODO_APLICAR`) |

## Referências

- [reference.md](reference.md) — grep, templates, exemplos, testes
- `.cursor/rules/015-db-session-auto.mdc`
- `.cursor/rules/040-crud-auto.mdc`
- `.cursor/rules/045-crud-transaction-commit-auto.mdc`
- Skill `executar-tarefa-template-fastapi`
