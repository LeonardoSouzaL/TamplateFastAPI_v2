# Modos e Prompts

Se o usuário não informar modo, usar `MODO_ANALISAR`.

## MODO_ANALISAR (padrão)
- Objetivo: mapear estrutura FastAPI e endpoints sem alterar código.
- Entrada: código atual e docs do projeto.
- Saída: inventário técnico, grupos de endpoint e lacunas.
- Restrições: somente leitura.

## MODO_ENTREVISTAR
- Objetivo: validar contexto funcional em lotes pequenos por módulo.
- Entrada: endpoints detectados no `MODO_ANALISAR`.
- Saída: processo, consumidores, dependências, criticidade e impacto (confirmados ou pendentes).
- Restrições: não travar por resposta incompleta; manter pendências explícitas.

## MODO_DOCUMENTAR
- Objetivo: gerar/atualizar documentação em `docs/api-process-map`.
- Entrada: dados técnicos + validação funcional disponível.
- Saída: `endpoint-catalog.yml`, docs por endpoint/processo, matriz, pendências e relatório.
- Restrições: marcar toda incerteza como `pendente_validacao_usuario`.

## MODO_SWAGGER_PROPOR
- Objetivo: propor melhorias de Swagger/OpenAPI e schemas Pydantic sem aplicar.
- Entrada: rotas, schemas e padrões existentes.
- Saída: diff proposto com impacto, arquivos alvo e riscos.
- Restrições: sem edição de arquivos.

## MODO_SWAGGER_APLICAR
- Objetivo: aplicar melhorias documentais em rotas/schemas quando autorizado.
- Entrada: aprovação explícita do usuário + proposta validada.
- Saída: decorators e schemas aprimorados (`summary`, `description`, `responses`, exemplos etc.).
- Restrições:
  - não alterar regra de negócio, query, autenticação ou contrato sem validação explícita;
  - detectar Pydantic v1/v2 antes de editar;
  - não misturar padrões v1 e v2;
  - preservar `operation_id` estável quando houver risco de consumidores externos;
  - não reduzir o Example Value do Swagger com `json_schema_extra.examples` ou `Field(examples=...)` mínimo no model raiz — preferir exemplo auto-gerado pelo schema;
  - marcar campos obrigatórios via tipo/`Field` conforme uso real no handler, não via exemplo parcial.

## MODO_VALIDAR
- Objetivo: medir completude e consistência da documentação.
- Entrada: artefatos em `docs/api-process-map`.
- Saída: status por endpoint, pendências e recomendações priorizadas.

## MODO_SYNC
- Objetivo: sincronizar fontes locais (`catalog`, docs e pendências) sem publicar em sistemas externos.
- Entrada: artefatos de documentação.
- Saída: consistência entre arquivos e atualização de índices.

## MODO_RELATORIO
- Objetivo: consolidar visão executiva/técnica do estado da API.
- Entrada: catálogo, matriz, pendências e status.
- Saída: resumo de cobertura, riscos e próximos passos.

## Modos de Mural interno

### MODO_MURAL_BOOTSTRAP_ENV
- Ler presets de [mural-presets.yml](mural-presets.yml) — **sem depender de `.env`**.
- Pergunta única ao usuário (se não informado): **homolog ou prod?**
- Resolver `api_base_url`, `target_group_id` e `created_by_id` do preset escolhido.
- Em `prod`, exigir confirmação explícita adicional antes do primeiro upsert.
- Override manual somente quando o usuário pedir valores diferentes do preset.
- Não bloquear por ausência de variáveis de ambiente.

### MODO_MURAL_ANALISAR
- Planejar árvore de publicação (raiz + subitens + `sort_order`) sem enviar.
- Validar `external_id`, `doc_kind`, `status`, `doc_version` e parent esperado por item.

### MODO_MURAL_PUBLICAR
- Pré-requisito: executar `MODO_MURAL_BOOTSTRAP_ENV` e validar configuração mínima.
- Em `prod`, solicitar confirmação explícita adicional antes do primeiro upsert.
- Publicar raiz primeiro e subitens depois, via upsert por `external_id`.
- Aplicar paginação em lotes de subitens quando necessário.

### MODO_MURAL_ATUALIZAR
- Atualizar incrementalmente por `external_id`, preservando conteúdo manual fora de marcadores.
- Não mover item de pai sem campo de parent explícito no payload.

### MODO_MURAL_SYNC
- Pré-requisito: executar `MODO_MURAL_BOOTSTRAP_ENV` para confirmar conexão/alvo.
- Reconciliar `docs/api-process-map/mural-sync.yml` com API do Mural (raiz, filhos e ids internos).
- Atualizar rastreio local após sync (`children`, `mural_id`, `last_sync_at`).

### MODO_MURAL_VALIDAR
- Comparar repositório vs Mural para raiz, filhos, status, versão e ordenação.
- Reportar divergências de árvore, parent e `sort_order` antes de publicar.

## Prompt-base por modo
Use sempre:
1. objetivo do modo;
2. escopo (módulo, endpoints ou processo);
3. restrições de segurança e governança;
4. formato de saída esperado.

Exemplo curto:
```text
Executar MODO_DOCUMENTAR no módulo Clientes.
Gerar/atualizar endpoint-catalog.yml, docs por endpoint e pendencias.
Manter pendente_validacao_usuario quando faltar confirmação funcional.
Não alterar código de produção.
```

Prompt-base para publicação hierárquica:
```text
Executar MODO_MURAL_BOOTSTRAP_ENV.
1) Se ambiente não informado, perguntar: homolog ou prod?
2) Carregar preset de mural-presets.yml
3) Se prod, confirmar explicitamente antes do primeiro upsert
4) Confirmar apto_para_publicacao
5) Executar MODO_MURAL_SYNC
6) Upsert raiz FASTAPI_DOC__{PROJECT}__ROOT__manual
7) Upsert subitens com parent_external_id do raiz
8) Validar children ordenados por sort_order
9) Atualizar docs/api-process-map/mural-sync.yml (campo environment)
Não desativar itens sem pedido explícito.
```

Prompt-base quando ambiente não foi informado:
```text
Executar MODO_MURAL_BOOTSTRAP_ENV.
Perguntar apenas: homolog ou prod?
Usar mural-presets.yml — não pedir variáveis de ambiente.
Se prod, aguardar confirmação explícita antes de publicar.
```
