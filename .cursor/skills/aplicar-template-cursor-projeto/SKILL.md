---
name: aplicar-template-cursor-projeto
description: Aplica as Cursor Rules e o template FastAPI em projetos já existentes — copiar arquivos, analisar estrutura, migrar módulo a módulo e manter release notes. Use ao adotar o template em projeto legado ou quando o usuário perguntar como aplicar as rules em projeto existente.
---

# Aplicar template Cursor em projeto existente

## Objetivo

Orientar a adoção incremental das Cursor Rules e do padrão FastAPI (`Endpoint -> Service -> CRUD -> Banco`) em projetos já em andamento, sem refatorar tudo de uma vez.

## Passo 1: copiar os arquivos

Copie para a raiz do projeto:

```text
.cursor/
AGENTS.md
.cursorrules
```

A pasta `.cursor/rules/` deve conter os arquivos `.mdc` completos.

### Padrão `.env` + debug (FastAPI start manual)

Para projetos que sobem com `uvicorn`/`python main.py`, inclua também:

```text
.cursor/rules/085-fastapi-env-debug-manual.mdc
docs/cursor/templates/launch.json
docs/cursor/templates/env-example-header.env
docs/cursor/templates/ci.yml
```

Prompt recomendado após copiar a rule:

```text
Use a Skill migrar-env-debug-fastapi (ou rule 085-fastapi-env-debug-manual.mdc).
Adapte este projeto: migre secrets para .env, crie .env.example, core/example-config.py,
.vscode/launch.json e documente execução + debug no README.
ROOT_PATH prod: /api-{nome}; homolog: /hg-api-{nome}.
PSQL_HOST prod: {host}; homolog: {host}.
Não versionar .env nem core/config.py real.
```

Templates prontos para copiar/adaptar: `docs/cursor/templates/launch.json`, `docs/cursor/templates/env-example-header.env`, `docs/cursor/templates/ci.yml`.

### Sessão async SQLAlchemy

Para projetos com `AsyncSession`, inclua também:

```text
.cursor/rules/015-db-session-auto.mdc
docs/cursor/templates/db/
```

Prompt recomendado:

```text
Use a rule 015-db-session-auto.mdc.
Configure db/session.py e api/deps.py (DbDep) conforme docs/cursor/templates/db/.
Não faça auto-commit em get_db se o CRUD já commita.
```

## Passo 2: abrir o projeto pela raiz

Abra no Cursor a pasta raiz do projeto, não uma subpasta.

Correto:

```text
meu-projeto-fastapi/
```

Evite abrir diretamente:

```text
meu-projeto-fastapi/api/
```

## Passo 3: analisar antes de refatorar

Use o prompt:

```text
Leia as rules do projeto e analise a estrutura atual. Não altere arquivos ainda. Me diga quais partes já seguem o padrão Endpoint -> Service -> CRUD -> Banco e quais precisam ser adaptadas.
```

## Passo 4: migrar módulo por módulo

Não refatore tudo de uma vez. Escolha um módulo pequeno e aplique:

```text
Endpoint -> Service -> CRUD -> Banco
```

Depois adicione testes e atualize o README.

## Mantendo release notes no README

Quando uma alteração relevante for feita, mantenha a seção:

```md
## Alterações recentes
```

Com tabela:

```md
| Data | Tipo | Módulo/Pasta | Alteração | Impacto |
| ---- | ---- | ------------ | --------- | ------- |
```

Use essa tabela para registrar novas pastas, módulos, endpoints, integrações, variáveis de ambiente e mudanças arquiteturais importantes.

## Descobrir regras de negócio de projeto existente

Depois de copiar as rules para um projeto já em andamento, use a Skill **`descobrir-regras-negocio`** (ou rule `120-business-rules-discovery-manual.mdc`) antes de criar novos endpoints em domínios com regras espalhadas.

Prompt recomendado: ver `docs/cursor/PROMPTS.md` (seção "Analisar regras de negócio de projeto existente").

Quando uma nova regra de negócio for confirmada durante o desenvolvimento, atualize uma rule de negócio existente ou crie uma nova rule específica.

## Criar abstrações reutilizáveis no core

A rule `115-reusable-core-abstractions-auto.mdc` orienta o Cursor a avaliar novas classes antes de criá-las.

Se a classe for reutilizável, por exemplo envio de e-mail, storage, PDF, QR Code, mensageria, cache, autenticação externa ou client genérico, considere criar em `core/` como classe abstrata ou base reutilizável.

Se a classe for regra de negócio de um módulo específico, mantenha em `services/`.

## Uso opcional de `.cursor/business-rules/`

Em projetos já em andamento, pode ser útil criar a pasta:

```text
.cursor/business-rules/
```

Ela deve ser usada como área de documentação e rascunho para regras de negócio descobertas durante a análise do projeto.

Use essa pasta para:

- regras descobertas ainda não transformadas em rule;
- perguntas pendentes para o usuário ou time de negócio;
- decisões de negócio tomadas durante a implementação;
- lista de rules candidatas.

Atenção: o Cursor carrega as Project Rules a partir de `.cursor/rules/*.mdc`. Portanto, regras confirmadas que precisam orientar novas implementações devem virar `.mdc` dentro de `.cursor/rules/`.

Fluxo recomendado:

```text
Análise do projeto -> .cursor/business-rules/ -> confirmação -> .cursor/rules/2xx-business-<dominio>-auto.mdc
```

## Links úteis

- [Índice das rules](../../docs/cursor/rules-index.md)
- [Prompts recomendados](../../docs/cursor/PROMPTS.md)
- [Skills do projeto](../)
- [Observabilidade — referência](../../docs/observability/reference.md)
- [Abstrações core](../../docs/cursor/core-abstractions.md)

## Saída esperada

1. Plano incremental de migração (módulos, prioridade, riscos)
2. Lista de arquivos copiados ou criados
3. Próximo módulo sugerido para refatoração
4. Atualização do README com **Alterações recentes**, se aplicável
