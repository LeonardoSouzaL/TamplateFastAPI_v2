# Draft: atualizações pendentes em rules `.mdc`

**Status (2026-06-02):** **Fase 2.5** e **Fase 3** aplicadas — `advance_romaneio`, mapas duplos, RECEIVE pré `PRE_RECEIVED`, RETURN legado → `DISPATCHED`, **`PARTIALLY_RECEIVED`** + `receive_summary`.

## `210-business-romaneios-auto.mdc`

- **`READY` deprecated/legado** — novos fluxos PA→CD → `AWAITING_COLLECTION`.
- **Bag-técnico** — sem acoplamento romaneio; ver rule `200`.
- **PA/CD** — validação externa; API não bloqueia nesta fase.
- **`PARTIALLY_RECEIVED`** — finish RECEIVE parcial + `receive_summary`; pendentes **sem fluxo adicional por enquanto** (P4). **Implementado Fase 3.**
- **`PROCESSING_ERROR`** — falha após `IN_PROCESSING` no finish; log retentável; permitir retentativa.
- Enum: `PARTIALLY_RECEIVED`, `PROCESSING_ERROR` (ambos no schema).

## `200-business-movements-auto.mdc`

### Bag-técnico

- Entrada `IN`; consulta `GET /items/search-by-movement`; sem romaneio.

### COLLECTION_REQUEST / COLLECTION_REQUEST_RECEIVED (Fase 2.5)

- **`COLLECTION_REQUEST`** via finish: rom `READY` → `COLLECTION_REQUESTED`; sem movimento de item.
- **`COLLECTION_REQUEST_RECEIVED`**: item → `READY_FOR_COLLECTING`; rom → `AWAITING_COLLECTION`.
- Movement API: recebimento, delivery, APP — **sem** orchestration PA→CD.

### RECEIVE parcial (Fase 3 — implementado)

- `update_rom_by_movement` valida **somente itens processados** (`ck=True`).
- Romaneio: todos ck → `RECEIVED`; algum ck false → `PARTIALLY_RECEIVED`.
- Resposta finish inclui `receive_summary`.

### Falha de processamento

- Finish com erro → romaneio `PROCESSING_ERROR` + log (não ficar em `IN_PROCESSING`).
