# Rules do Cursor

Esta pasta contém as Project Rules usadas pelo Cursor para orientar a geração, alteração e revisão de código neste padrão FastAPI.

As rules reais são os arquivos `.mdc`. Este `README.md` é apenas documentação para o time.

**Skills de workflow:** `.cursor/skills/` — ver [índice](../../docs/cursor/rules-index.md) e [README das skills](../skills/README.md).

## Como o Cursor aplica as rules

Cada arquivo `.mdc` possui um cabeçalho com:

```yaml
---
description: Descrição da rule
globs: "padrão de arquivos"
alwaysApply: true ou false
---
```

- `alwaysApply: true`: a rule entra como contexto global (stubs curtos para workflows longos).
- `alwaysApply: false`: a rule é aplicada conforme o arquivo/escopo indicado em `globs` ou quando o Agent julgar relevante.
- Workflows operacionais longos: **Skill** em `.cursor/skills/` (rules manuais/auto são stubs que apontam para a Skill).

## Fluxo arquitetural esperado

Para operações de banco:

```text
Endpoint -> Service -> CRUD -> Banco
```

Para integrações externas:

```text
Endpoint -> Service -> Core Client -> API externa
```

## O que cada rule faz

### `005-rule-vs-skill-gate-always.mdc`

Gate global: antes de criar rule operacional grande, avaliar se o conteúdo deve ser **Skill** (`.cursor/skills/`), **docs** ou **Rule**. Questionar o usuário quando o pedido parecer workflow reutilizável.

### `000-project-context-always.mdc`

Define o contexto global do projeto: stack, camadas, fluxo arquitetural e regras gerais.

### `010-architecture-always.mdc`

Define regras de arquitetura, dependência entre camadas e como criar novos módulos.

### `015-db-session-auto.mdc`

Define sessão SQLAlchemy async: `create_async_engine`, `async_sessionmaker`, `get_db` e alias `DbDep`. Templates: `docs/cursor/templates/db/`.

### `020-fastapi-endpoints-auto.mdc`

Define o padrão para endpoints FastAPI leves, sem regra de negócio pesada.

### `030-services-auto.mdc`

Define como criar services com validações, normalizações, orquestração e regras de negócio.

### `040-crud-auto.mdc`

Define que CRUD deve cuidar apenas de acesso ao banco, filtros, paginação e persistência.

### `045-crud-transaction-commit-auto.mdc`

Define `commit: bool` no CRUD base, transação única no service/endpoint e separação sessão vs commit (complementa rule 015).

Para auditar legado e montar/aplicar plano de migração: Skill `migrar-transacao-crud-fastapi` (`.cursor/skills/migrar-transacao-crud-fastapi/`).

### `050-schemas-models-auto.mdc`

Define separação entre schemas Pydantic e models SQLAlchemy, além do padrão Base/Create/Update/Response.

### `055-datetime-timezone-auto.mdc`

Padrão datetime/timezone: UTC no banco (`DateTime(timezone=True)`), `utc_now()`, `SPDateTime`/`OptionalSPDateTime` em schemas `*Response`. Templates: `docs/cursor/templates/datetime/`.

### `060-core-integrations-auto.mdc`

Define regras para clients externos, OAuth2, API Key, Bearer Token, Basic Auth, certificados, mTLS e tratamento de erro externo.

### `070-tests-auto.mdc`

Define estrutura e padrão de testes usando pytest, AsyncMock e testes por camada.

### `075-github-actions-ci-auto.mdc`

Stub por glob — aponta para Skill `configurar-ci-github-actions`. Princípios: pytest unitário, UTF-8 em requirements, `ci.yml` separado de deploy. Template: `docs/cursor/templates/ci.yml`.

### `080-security-config-always.mdc`

Define regras globais de segurança para não versionar secrets, tokens, senhas, certificados ou `.env` real.

### `081-api-messages-no-internal-ids-auto.mdc`

Em Supplies, Chamados Indoor e Recebimento de carga, `detail`/`message` de operador não interpolam PK numérico. Serial, SKU, protocolo, quantidade e saldo permanecem. IDs ficam no JSON e nos logs.

### `085-fastapi-env-debug-manual.mdc`

Stub manual — Skill `migrar-env-debug-fastapi`. Invocar `@085-fastapi-env-debug-manual` para `.env`, `example-config`, `launch.json`.

### `090-docs-readme-auto.mdc`

Define padrões para documentação e READMEs por pasta, evitando redundância.

### `095-project-readme-sync-auto.mdc`

Define regras para manter o README real do projeto atualizado, incluindo uma tabela de `Alterações recentes`.

### `100-task-workflow-agent.mdc`

Stub manual — Skill `executar-tarefa-template-fastapi`. Fluxo para tarefas multi-camada no template.

### `110-python-style-auto.mdc`

Define estilo geral para código Python, imports, async, logs, erros e organização.

### `115-reusable-core-abstractions-auto.mdc`

Stub por glob — princípios curtos; detalhes em `docs/cursor/core-abstractions.md`. Avaliar se nova classe vai para `core/` ou `services/`.

### `120-business-rules-discovery-manual.mdc`

Stub manual — Skill `descobrir-regras-negocio`. Mapear regras de negócio em projeto legado e propor rules `2xx-business-*`.

### `130-fastapi-swarm-deploy-manual.mdc`

Stub manual — Skill `deploy-swarm-fastapi`. Gate: perguntar `APP_PORT`, `STACK_NAME`, ASGI antes de gerar arquivos. Contexto: `docs/contexto_infra_swarm_cursor.md`.

### `131-docker-swarm-stack-auto.mdc`

Stub por glob — Skill `deploy-swarm-fastapi`. Dockerfile, stack, `.dockerignore`, `.env.example`.

### `132-github-actions-swarm-deploy-auto.mdc`

Stub por glob — Skill `deploy-swarm-fastapi`. Workflow `deploy-swarm.yml` separado de `ci.yml`.

### `333-observability-otel-loki-always.mdc`

Rule global (always) com **princípios** OTEL/Tempo/Loki. Implementação: Skill `implementar-otel-loki-fastapi` + `docs/observability/reference.md`.

### Rules de negócio `2xx` (específicas deste projeto)

#### `201-business-lastmile-metrics-auto.mdc`

Métricas LastMile somente leitura: KPIs iguais à Transportes v2 (`pending`, `without_driver`, `finished`, atraso por `end_date`, tempo médio), filtros SQL, default de `order_type`, sem migration/escrita.

#### `202-business-lastmile-os-status-auto.mdc`

Totais de OS LastMile por status da ordem (`GET /lastmile/orders/by-status`): fato `service_order`, PENDING só `UPPER(type)='PENDING'`, `finished` aberto/encerrado, visão ILIKE (`COLLECT`/`NORMAL`/`DESINSTAL%`/`RETIRADA%`), sem misturar com KPIs de viagem.

#### `203-business-lastmile-os-pa-auto.mdc`

Totais de OS LastMile por PA (`GET /lastmile/orders/by-pa`): fato `service_order`, `designacao` via GAI, SLA `created_at` + `estimated_deadline`, rankings `pa_ofensora`/`ofensoras` e `melhor_pa`/`melhores` em memória, sem misturar com KPIs de viagem nem com `by-status`.

#### `204-business-lastmile-driver-auto.mdc`

Totais de viagens LastMile do dia por técnico (`GET /lastmile/dashboard/driver-status-summary`): fato `order_travels`, `driver_id` = `auth_app.uid`, atraso por `end_date`, SLA e status no SQL, filtro de PA da viagem, sem misturar com totais de OS.

#### `205-business-lastmile-os-client-auto.mdc`

Totais de OS LastMile por cliente (`GET /lastmile/orders/by-client`): fato `service_order`, `cliente` via GAI, mesma visão e SLA do `by-pa`, rankings `cliente_ofensor`/`ofensores` e `melhor_cliente`/`melhores` em memória, endpoint novo sem alterar `by-status` / `by-pa`.

#### `206-business-lastmile-os-driver-auto.mdc`

Totais de OS LastMile por técnico (`GET /lastmile/orders/by-driver`): fato `service_order`, `tecnico` via `auth_app.uid`, mesma visão e SLA do `by-client`, ociosidade (`last_opening` + rota do dia + carência de 50 min), rankings `tecnico_ofensor`/`ofensores`, `melhor_tecnico`/`melhores` e `tecnico_ocioso`/`ociosos`, endpoint novo sem alterar `by-status` / `by-pa` / `by-client` nem `driver-status-summary`.

#### `207-business-lastmile-os-overview-auto.mdc`

Visão geral de OS LastMile (`GET /lastmile/orders/overview`): fato `service_order` sem agrupamento, pendente/atendida por `end_date` da viagem atual, SLA compartilhado, percentuais sobre `total` e efetividade no service, filtros de PA e cliente da OS, endpoint novo sem alterar `by-status` / `by-pa` / `by-client` / `by-driver`.

#### `200-business-movements-auto.mdc`

Regras de movimentações: mapa `MovementType` → status do item/romaneio, criação de item em `IN`/`COLLECTED`, `IN_DEPOT` e `ignore_status_rule`, distinção `movement_type=RETURN` vs `project_name=REVERSA`, erros 400/404/424.

#### `210-business-romaneios-auto.mdc`

Regras de romaneios (v1 legado e v2): formato `romaneio_number`, inserção só em `STARTED`, bloqueio em romaneio `STARTED`/`READY`, finish (`RETURN`/`TRANSFER`/`RECEIVE`), resposta finish com **`status_rom` real**, filtro listagem **`CANCELLED`**, v1 somente manutenção (decisões 2026-06-01).

#### `215-business-transport-integration-auto.mdc`

Integração Abertura v2 (`COLLECTION_REQUEST` + `action=approve`), tracking v3 no `READY_FOR_PICKUP` e POST `integration_system/status` da viagem **só** no pronto para coleta (`TRANSPORT_INDOOR_READY_TRAVEL_STATUS`, sem `status_os`). Collect/cancel não alinham viagem. Diagnóstico: `GET /stock-requests/{id}/transport`. Contrato `docs/abertura-v2-stock.md` / `docs/tracking-v3-stock.md` / `docs/spec-stock-atualizar-viagem.md`. Handoff Transportes: `docs/tracking-v3-ready-for-pickup-transportes.md`.

#### `220-business-cielo-sap-auto.mdc`

Regras Cielo/SAP: consulta síncrona, serial provisório `ILG-*`, **`product_id` obrigatório para CHIP em IN**, `extra_info.measures`, picking `delivery/{serial}`, `StockErrors` (picking Cielo; divergência depósito SAP esperada).

#### `230-business-catalog-auto.mdc`

Regras de catálogo: produto duplicado SKU+description → 423, measures Cielo, `OrderOrigin` (`origin_name`, `project_name`, `stock_type`), catálogo de origens `client_id=1`, padrão reversa `arancia` + `REVERSA`; `EVENTS_INTELIPOST` só referência em config.

#### `240-technician-bag-auth-app-location.mdc`

Bag do técnico: no POST add serial, `created_by` = `auth_app.uid` resolve `gai_id` como location quando `to_location_id` não é informado.

#### `250-business-claro-indoor-auto.mdc`

Claro Indoor: catálogo de status/transições por `process_code`, `romaneio.extra_info`, `RomaneioEvent` global (`record_romaneio_event`), paginação `PaginationMeta`, validação de pipeline via tabelas (não hardcode). Endpoints `/api/v1/claro/indoor` (uploads, examples/templates, romaneios, produtos). Spec: `docs/claro-indoor-spec.md`. Pendência: migrar PA→CD para `process_code=PA_CD`.

#### `260-business-supply-control-auto.mdc`

Supply Control: insumos não serializáveis com saldo quantitativo (`logistic_stock_supplies`), flag `extra_info.supplies=true`, movimentações ENTRY/EXIT/TRANSFER, gate no Movement API. Endpoints `/api/v1/supplies*`.

#### `270-business-stock-requests-auto.mdc`

Chamados Indoor (preparação de materiais): `/api/v1/stock-requests` create/prepare/collect. **Não** mistura com recebimento de carga (rule `271`).

#### `271-business-inbound-receipt-auto.mdc`

Recebimento de carga: `POST /inbound-alerts` (pré-alerta Transportes, só aviso) e `POST /{id}/receive` (ENTRY só de supply no PA/CD). Serial aceito e ignorado nesta fatia. Contrato: `docs/pre-alerta-recebimento-transportes.md`.

#### `272-business-fulfillment-dce-auto.mdc`

DCE Fulfillment nos Chamados Indoor: só se `request_type.dace=true` (coluna no tipo; default false). Emitida no `OPEN` (qty solicitada), `GET /api/v2/dce/status` no `READY_FOR_PICKUP` e cancel automático no `CANCELLED` se `extra.dce.ok`. `POST /{id}/dce` é retry. Não mistura com Claro Indoor reversa nem com `volumn_product_for_dce`.

#### `273-business-stock-request-labels-auto.mdc`

Etiquetas A4 dos volumes Indoor: `GET /{id}/labels` (JSON com URL) e `GET /{id}/labels/file` (PDF gerado na hora). Uma página por volume ativo. Spec: `docs/stock-requests-etiquetas-front.md`.


## Sobre `.cursor/business-rules/`

É permitido criar uma pasta auxiliar:

```text
.cursor/business-rules/
```

Essa pasta serve para documentação de apoio sobre regras de negócio descobertas em projetos existentes, como perguntas pendentes, decisões e rascunhos.

Ela **não deve substituir** `.cursor/rules/`.

- Rules ativas do Cursor: `.cursor/rules/*.mdc`
- Documentação auxiliar de negócio: `.cursor/business-rules/*.md`

Quando uma regra de negócio for confirmada e precisar orientar o Cursor em futuras alterações, crie ou atualize uma rule `.mdc` em `.cursor/rules/`, normalmente no padrão:

```text
.cursor/rules/2xx-business-<dominio>-auto.mdc
```

## Quando criar uma nova rule

Crie uma nova rule quando houver um padrão recorrente que o time quer aplicar automaticamente, por exemplo:

- padrão específico de autenticação;
- padrão de mensageria;
- padrão de migrations;
- padrão de workers/jobs;
- padrão de deploy;
- padrão de logs/auditoria;
- regra de negócio específica de um domínio;
- regra reutilizável descoberta em projeto existente.

## Quando não criar uma nova rule

Não crie rule para uma orientação pontual ou temporária. Nesse caso, documente em `docs/` ou no README da pasta específica.

## Importante

- Rules **always** e rules por **camada** (020–070) mantêm instruções completas no `.mdc`.
- Rules de **workflow longo** são **stubs** — implementação nas Skills e em `docs/`.
- Índice principal para entry points: `docs/cursor/rules-index.md`.
- Não duplicar workflow inteiro em nova rule — usar Skill (rule `005-rule-vs-skill-gate-always.mdc`).
