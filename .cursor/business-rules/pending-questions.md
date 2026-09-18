# Perguntas pendentes sobre regras de negócio

| Data | Domínio | Pergunta | Status | Resposta |
| ---- | ------- | -------- | ------ | -------- |
| 2026-08-10 | Chamados Indoor | Notificações (solicitante / responsável retirada) — precisa fazer? Canal? | Respondida | Hint na API (não envia e-mail): `notification` em approve/reject/complement/`READY_FOR_PICKUP`; front envia SMTP; pickup teste `ti@c-trends.com.br`; sem Qualitor; não bloqueia go-live. |
| 2026-08-05 | Chamados Indoor | Coleta com assinatura / movimento de estoque na coleta? | Respondida | Implementado (2026-08-07): `POST /{id}/collect` com coletor/comprovante/assinatura; EXIT supply + serial→`IN_TRANSIT`; status `COLLECTED`. |
| 2026-08-05 | Chamados Indoor | Aprovação formal por tipo (`approval_required`)? | Respondida | Implementado (2026-08-06): create em `AWAITING_APPROVAL`; actions approve/complement/reject/resubmit; PATCH em complemento. |
| 2026-06-01 | Romaneio | Em que momento o romaneio passa de `STARTED` para `READY`? | Respondida | **`READY` é deprecated/legado** — manter enum e bloqueios; novos fluxos PA→CD não usam READY. Bipagem encerra com finish `RETURN` → `AWAITING_COLLECTION`. Quem seta READY hoje é integrador/processo externo legado. |
| 2026-06-01 | Romaneio | O status cancelado no banco é `CANCELLED` ou `CANCELADO`? | Respondida | Canônico: **`CANCELLED`**. |
| 2026-06-01 | Movimentação | POST unitário `RETURN` vs batch `REVERSA` para atualizar romaneio? | Respondida | Campos distintos; alinhar POST unitário na Fase 1. |
| 2026-06-01 | Romaneio finish | `RomaneioFineshedResponse` retorna status real? | Respondida | Sim — `status_rom` real após `update_rom_by_movement`. |
| 2026-06-01 | Romaneio v1 | v1 recebe novas features? | Respondida | v2 para novas; v1 manutenção. |
| 2026-06-01 | Segurança | API sem auth intencional? | Respondida | Sim — rede/gateway. |
| 2026-06-01 | Intelipost | `EVENTS_INTELIPOST` usado? | Respondida | Não nesta API. |
| 2026-06-01 | Cielo | CHIP em falha SAP? | Respondida | `product_id` obrigatório; sem ILG. |
| 2026-06-01 | Movimentação | `ignore_status_rule`? | Respondida | Uso excepcional. |
| 2026-06-01 | Origem | Catálogo `order_origin`? | Respondida | Banco; ver rule `230`. |
| 2026-06-01 | Catálogo | Cliente em GAI? | Respondida | GAI `arancia_client`. |
| 2026-06-01 | Erros | `StockErrors` em todos os fluxos? | Respondida | Só picking Cielo hoje. |
| 2026-06-01 | Regras passadas | Incidentes prioritários? | Respondida | 12.1–12.5 documentados. |
| 2026-06-01 | Bag-técnico | Bag acoplado ao romaneio? | Respondida | **Não.** Entrada `IN`; consulta `search-by-movement` por `created_by` — visão estoque, não romaneio. |
| 2026-06-01 | Romaneio | API valida PA→CD? | Respondida | **Não nesta fase.** Responsabilidade do chamador (`group_id`). |
| 2026-06-01 | Movimentação | PRE_COLLECT vs COLLECTION_REQUEST vs status romaneio? | Respondida | **`MovementType.COLLECTION_REQUEST`** via finish (`POST /v2/romaneios/finish/{n}`) → rom **`COLLECTION_REQUESTED`**. Não usar PRE_COLLECT. Movement API não é o caminho PA→CD para solicitação de coleta. |
| 2026-06-01 | Romaneio | Recebimento parcial no finish RECEIVE? | Respondida | **`PARTIALLY_RECEIVED`** se algum `ck=false`; **`RECEIVED`** se todos `ck=true`; resumo (`receive_summary`) na resposta API. Implementado na Fase 3. |
| 2026-06-01 | Movimentação | Item status após solicitação de coleta? | Respondida | Finish **`COLLECTION_REQUEST_RECEIVED`** → item **`READY_FOR_COLLECTING`** (não `IN_DEPOT`/`IN_TRANSIT`). |
| 2026-06-01 | Romaneio | Romaneio status após solicitação de coleta? | Respondida | Finish **`COLLECTION_REQUEST`** → **`COLLECTION_REQUESTED`**; finish **`COLLECTION_REQUEST_RECEIVED`** → **`AWAITING_COLLECTION`**. |
| 2026-06-01 | Transportes | Gatilho após `AWAITING_COLLECTION`? | Pendente | Módulo externo — Fase 4. |
| 2026-06-01 | Romaneio | Itens pendentes após `PARTIALLY_RECEIVED`? | Respondida | **Por enquanto, nada** — sem segundo finish, cancelamento ou ocorrência nesta fase. |
| 2026-06-01 | Romaneio | Finish parcial / romaneio em `IN_PROCESSING`? | Respondida | RECEIVE parcial: validar só itens `ck=True`; status `PARTIALLY_RECEIVED` ou `RECEIVED`. Falha técnica: **`PROCESSING_ERROR`** + log para retentativa (não permanecer em `IN_PROCESSING`). |
| 2026-07-23 | Romaneio / catálogo | Migrar hardcodes PA→CD (`_ADVANCE_ROMANEIO_TRANSITIONS` / mapas finish em `services/romaneio.py` e `movement.py`) para `process_code=PA_CD` nas tabelas `logistic_stock_romaneio_status` + `logistic_stock_romaneio_status_transition`? | Pendente | **Fora desta leva Claro Indoor.** Nesta leva só seed/`assert_indoor_transition` para **INDOOR**. Follow-up: seed `PA_CD` + trocar hardcodes do finish/insert/`_ACTIVE_ROMANEIO_BLOCKING_STATUSES` pelo helper de transição do catálogo. Spec: `docs/claro-indoor-spec.md` §3; rules `210`/`250`. |
| 2026-07-23 | Claro Indoor | GAI origem `ClaroReversa` cadastrado? | Respondida | **Corrigido em 2026-08-05:** ClaroReversa foi criado por engano. Origem passa a ser PA selecionável; migration `e2f3a4b5c6d7` remapeia dados e remove o GAI (HG primeiro; prod após validação). |
