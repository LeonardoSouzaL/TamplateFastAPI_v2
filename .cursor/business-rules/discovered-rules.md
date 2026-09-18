# Regras de negócio descobertas — stock-api

Análise em **2026-06-01**. Rules ativas criadas: `200`–`230-business-*-auto.mdc`.

## 1. Módulos principais

| Camada | Módulos / rotas | Papel |
| ------ | ----------------- | ----- |
| **API v1** | `clients`, `products`, `origins`, `movements`, `items`, `romaneios` (v1), `item/provisional`, `locations` | CRUD e consultas legadas |
| **API v2** | `romaneios` | Fluxo de reversa: criar romaneio, CK, extra-item, finish, listagem |
| **Services** | `movement.py`, `romaneio.py`, `item.py`, `consulta_sincrona.py` | Regras de negócio concentradas |
| **CRUD** | `baseAsync.py` + `crud_*` | Acesso PostgreSQL (`SessionLocal_psql`) |
| **Models** | `item`, `movement`, `romaneio`, `romaneio_item`, `product`, `client`, `origin`, `location`, `errors`, `provisional_serial` | Tabelas `logistic_stock_*` e `logistica_*` |
| **Core** | `config`, `request`, `filters`, `logging` | Settings, client HTTP, observabilidade |
| **DB extra** | `deps.get_db_211`, `get_db_ag_ws` | SQL Server (legado/integrações) |
| **Migrations** | `alembic-hg`, `alembic-prod` | Dois tracks de schema |

Domínio central: **estoque logístico** (itens + movimentações) e **romaneios de reversa** (volume/kit, CK, finalização em lote).

---

## Regras confirmadas

| Domínio | Regra | Fonte | Rule `.mdc` |
| ------- | ----- | ----- | ----------- |
| Arquitetura | `Endpoint -> Service -> CRUD` | `.cursorrules`, README | `010` (existente) |
| Movimentação | Mapa `MovementType` → `Item.status` em `MovementService._get_status` | `services/movement.py` | `200` |
| Movimentação | `IN` / `COLLECTED` criam item; demais exigem item (424) | `services/movement.py` | `200` |
| Movimentação | Exceto `IN`, `COLLECTED`, `DELIVERY`: exige `IN_DEPOT` ou `ignore_status_rule` (uso excepcional) | `services/movement.py` + decisão 2026-06-01 | `200` |
| Movimentação | `movement_type=RETURN` ≠ `project_name=REVERSA` (campos distintos) | Decisão time 2026-06-01 | `200`, `210`, `230` |
| Movimentação | `move-list-items` + romaneio v2: origem `arancia` + `project_name=REVERSA` | código + decisão time | `200`, `210` |
| Romaneio | Número AR* gerado no `before_insert` por `client_id` | `models/romaneio_model.py` | `210` |
| Romaneio finish | Resposta HTTP com **`status_rom` real** após finish | Decisão time 2026-06-01 | `210` |
| Romaneio | Status cancelado: **`CANCELLED`** (filtro v2 alinhado) | Decisão time 2026-06-01 | `210` |
| Romaneio | v1 somente manutenção; v2 para features novas | Decisão time 2026-06-01 | `210` |
| Romaneio item | Inserção só em `STARTED`; serial UPPER; bloqueio em romaneio ativo (`STARTED`/`READY`/`COLLECTION_REQUESTED`/`AWAITING_COLLECTION`/`DISPATCHED`) em outro romaneio | `services/romaneio.py` | `210` |
| Romaneio v2 | Finish PA→CD via `advance_romaneio`; RECEIVE só `ck=True`, rom pré `PRE_RECEIVED`; parcial → `PARTIALLY_RECEIVED` | `romaneio_v2.py`, `services/romaneio.py` | `210` |
| Romaneio | **`READY` deprecated** — manter enum/bloqueio legado; novos fluxos PA→CD → `AWAITING_COLLECTION` | Decisão 2026-06-01 | `210` |
| Estoque | Bag-técnico = entrada `IN`; consulta `search-by-movement`; **sem** acoplamento romaneio | Decisão 2026-06-01 | `200` |
| Romaneio | Validação PA/CD **fora da API** (chamador via `group_id`) | Decisão 2026-06-01 | `210`, `230` |
| Romaneio finish | **`COLLECTION_REQUEST`** (finish) → rom **`COLLECTION_REQUESTED`**; sem movimento de item | Fase 2.5 | `210` |
| Romaneio finish | **`COLLECTION_REQUEST_RECEIVED`** (finish) → item **`READY_FOR_COLLECTING`**; rom **`AWAITING_COLLECTION`** | Fase 2.5 | `200`, `210` |
| Romaneio | **`PARTIALLY_RECEIVED`**: finish RECEIVE com algum `ck=false`; resumo na resposta; pendentes sem fluxo adicional (P4) | Fase 3 | `210` |
| Romaneio | Finish falho → **`PROCESSING_ERROR`** + log retentável (P5) | Decisão 2026-06-01 | `210` |
| Cielo | Consulta síncrona, ILG, measures, picking delivery | código + decisão 2026-06-01 | `220` |
| Cielo | CHIP: `product_id` obrigatório em `IN`; sem consulta SAP; sem ILG | Decisão time 2026-06-01 | `220` |
| Cielo | Divergência depósito SAP vs Arancia: esperada; `StockErrors` no picking | Decisão time 2026-06-01 | `220` |
| Erros | `StockErrors` só no picking Cielo hoje | Decisão time 2026-06-01 | `220` |
| Produto | Duplicidade SKU+description → 423; measures Cielo | `product.py` | `230` |
| Catálogo | Origens no banco; combinações `client_id=1` (ver tabela abaixo) | Decisão time 2026-06-01 | `230` |
| Config | `EVENTS_INTELIPOST`: referência em config, sem uso nos fluxos da API | Decisão time 2026-06-01 | `230` |
| Segurança | Sem auth FastAPI intencional | Decisão time 2026-06-01 | `080` (referência) |

---

## Catálogo `logistic_stock_order_origin` (`client_id = 1`, Cielo)

| origin_name | project_name | stock_type |
|-------------|--------------|------------|
| arancia | REVERSA | Aguardando Reversa |
| arancia | REVERSA | Aguardando Reversa (Seriais Provisórios) |
| intelipost | last_mile_b2c | Suprimento P/ Entrega |
| intelipost | last_mile_b2c | Aguardando Reversa |
| intelipost | last_mile_b2c | Aguardando Reversa (Seriais Provisórios) |
| sap | Caça_POS | Aguardando Reversa |
| sap | Caça_POS | Aguardando Reversa (Seriais Provisórios) |
| SAP | BAU | Suprimento P/ Entrega |

Nota: `sap` vs `SAP` coexistem no banco — filtros devem respeitar case exato. Unique: `(origin_name, project_name, client_id, stock_type)`.

---

## Regras prioritárias (incidentes / produção)

| ID | Regra | Rule `.mdc` |
| -- | ----- | ----------- |
| 12.1 | Seriais duplicados podem ocorrer fisicamente; bloqueio em romaneio ativo (`STARTED`/`READY`) em outro romaneio continua válido | `210` |
| 12.3 | Divergência depósito SAP (`LGORT`) vs depósito Arancia é comum (SAP assíncrono) — cenário esperado; picking grava `StockErrors` | `220` |

---

## Rules `.mdc` criadas

| Arquivo | Domínio |
| ------- | ------- |
| `.cursor/rules/200-business-movements-auto.mdc` | Movimentações |
| `.cursor/rules/210-business-romaneios-auto.mdc` | Romaneios / reversa |
| `.cursor/rules/220-business-cielo-sap-auto.mdc` | Cielo + SAP |
| `.cursor/rules/230-business-catalog-auto.mdc` | Catálogo (produto, origem, cliente, location) |
