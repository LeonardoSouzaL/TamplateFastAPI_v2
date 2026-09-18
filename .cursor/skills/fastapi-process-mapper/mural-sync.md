# Mural Sync

## Objetivo
Publicar e atualizar documentação técnica/funcional no Mural interno com hierarquia por projeto (`1 raiz + subitens`), sem duplicidade, usando `upsert-by-external-id` como padrão idempotente.

## Presets de ambiente (padrão — sem `.env`)
A skill **não exige** variáveis de ambiente para publicar no Mural. Os valores de homologação e produção estão em [mural-presets.yml](mural-presets.yml).

| Campo | Homologação | Produção |
|-------|-------------|----------|
| `api_base_url` | `https://192.168.0.214/hg-api-mural/api/v1/items` | `http://192.168.0.215/api-mural/api/v1/items` |
| `target_group_id` | `34` | `323` |
| `created_by_id` | `122` | `1037` |
| `requires_token` | `false` | `false` |

Resolução na skill:
1. Perguntar ao usuário apenas: **homolog ou prod?** (se ainda não informado).
2. Carregar o preset correspondente de `mural-presets.yml`.
3. Montar payloads com `created_by_id` e `ids: [target_group_id]` do preset.
4. Em **prod**, exigir confirmação explícita antes do primeiro upsert.
5. Override manual somente se o usuário pedir valores diferentes.

Observações:
- não pedir `MURAL_API_BASE_URL`, `MURAL_TARGET_GROUP_ID` nem `MURAL_CREATED_BY_ID` — já estão no preset;
- não criar nem exigir `.env` / `.env.example` para operação normal do Mural;
- se `requires_token` passar a `true`, solicitar token na hora (não versionar).

## Firebase (somente para anexos)
Quando houver upload de anexos, configurar no projeto (opcional):

```env
FIREBASE_STORAGE_BUCKET=seu-bucket.appspot.com
FIREBASE_CREDENTIALS_PATH=certs/firebase-service-account.json
FIREBASE_UPLOAD_BASE_PATH=fastapi-process-mapper
```

Para anexos, a skill envia arquivo para Firebase Storage e repassa ao Mural apenas a URL final.

## Bootstrap obrigatório antes de publicar
Antes de publicar/atualizar/sincronizar no Mural:

1. Ler `mural-presets.yml`.
2. Perguntar **somente** o ambiente (`homolog` ou `prod`) se o usuário não tiver informado.
3. Aplicar preset e confirmar resumo: ambiente, grupo e `created_by_id` (sem expor token).
4. Em prod, aguardar confirmação explícita adicional.
5. Prosseguir com upsert.

Resultado esperado do bootstrap:
- `apto_para_publicacao` quando ambiente resolvido (e prod confirmado);
- `bloqueado_por_config` apenas se prod sem confirmação ou override inválido.

## Campos de governança no payload
Incluir os campos de governança em todo item publicado:

```json
{
  "project_name": "TransportesAPI",
  "doc_kind": "overview|endpoint|process|report",
  "doc_version": "2026.07",
  "source": "skill_fastapi_process_mapper",
  "status": "draft|published|deprecated",
  "parent_id": null,
  "parent_external_id": null,
  "sort_order": 0
}
```

Regras:
- usar `summary` como campo padrão da skill (não depender de `description`);
- `doc_kind: overview` somente para o item raiz;
- `source` deve identificar a origem automática da publicação;
- `sort_order` deve ser estável para facilitar reorder e comparação.

## Padrão de `external_id` hierárquico
Manter prefixo `FASTAPI_DOC__{PROJECT}__...`:

| Tipo | `external_id` |
|------|---------------|
| Raiz | `FASTAPI_DOC__{PROJECT}__ROOT__manual` |
| Endpoint | `FASTAPI_DOC__{PROJECT}__ENDPOINT__{METHOD}__{PATH}` |
| Processo | `FASTAPI_DOC__{PROJECT}__PROCESSO__{NAME}` |
| Relatório | `FASTAPI_DOC__{PROJECT}__RELATORIO__status_documentacao` |

Normalização sugerida:
- endpoint `PATH`: sem `/` inicial, `/` e `-` para `_`, sem `{}` e sem acentos;
- `METHOD` em maiúsculo;
- manter tamanho `< 255` com abreviação determinística quando necessário.

## Rotas obrigatórias

| Operação | Rota |
|----------|------|
| Upsert idempotente | `PUT /api/v1/items/upsert-by-external-id/` |
| Buscar por `external_id` | `GET /api/v1/items/by-external-id/{external_id}` |
| Listar raízes | `GET /api/v1/items?only_roots=true&skip=0&limit=20` |
| Filhos por id do pai | `GET /api/v1/items/{id}/children?skip=0&limit=20` |
| Filhos por `external_id` do pai | `GET /api/v1/items/by-external-id/{external_id}/children?skip=0&limit=20` |
| Reorder em lote | `PUT /api/v1/items/reorder-children` |
| Soft-delete | `DELETE /api/v1/items/disable-item/{id}` (somente com pedido explícito) |

## Regras de parent
- aceitar `parent_id` ou `parent_external_id` para subitens;
- preferir `parent_external_id` na skill (mais estável entre ambientes);
- mover subitem de pai apenas quando o campo de parent vier explicitamente no payload;
- em update de conteúdo, não reenviar parent se não houver intenção de mover.

## Fluxo de publicação hierárquica
1. Upsert do item raiz (`parent_id: null`, `doc_kind: overview`).
2. Upsert de subitens (`doc_kind: endpoint|process|report`) com `parent_external_id` do raiz.
3. Validação dos filhos via rota `.../by-external-id/{pai}/children`.
4. Reorder opcional com `PUT /reorder-children` quando houver mudança de `sort_order`.

Não desativar item (`disable-item`) sem solicitação explícita.

## `sort_order` sugerido
- raiz: `0`
- seções fixas: overview interno `10`, matriz `20`, pendências `30`, relatório `40`
- endpoints: `100+` (incremental por módulo/tag)
- processos: `200+`

## Payload base para item raiz
```json
{
  "external_id": "FASTAPI_DOC__TransportesAPI__ROOT__manual",
  "title": "[TransportesAPI] Mapa da documentação",
  "summary": "Índice principal da documentação técnica e funcional da API TransportesAPI.",
  "content": "<h1>Mapa da documentação</h1><p>...</p>",
  "item_type": "manual",
  "severity": "informational",
  "target_type": "groups",
  "is_active": true,
  "is_indefinite": true,
  "created_by_id": 1,
  "ids": [323],
  "project_name": "TransportesAPI",
  "doc_kind": "overview",
  "doc_version": "2026.07",
  "source": "skill_fastapi_process_mapper",
  "status": "draft",
  "parent_id": null,
  "parent_external_id": null,
  "sort_order": 0
}
```

## Payload base para subitem
```json
{
  "external_id": "FASTAPI_DOC__TransportesAPI__ENDPOINT__GET__clientes",
  "title": "[TransportesAPI] GET /clientes — Documentação técnica",
  "summary": "Documentação técnica e funcional do endpoint GET /clientes da API TransportesAPI.",
  "content": "<h1>GET /clientes</h1><p>...</p>",
  "item_type": "manual",
  "severity": "informational",
  "target_type": "groups",
  "is_active": true,
  "is_indefinite": true,
  "created_by_id": 1,
  "ids": [323],
  "project_name": "TransportesAPI",
  "doc_kind": "endpoint",
  "doc_version": "2026.07",
  "source": "skill_fastapi_process_mapper",
  "status": "published",
  "parent_external_id": "FASTAPI_DOC__TransportesAPI__ROOT__manual",
  "sort_order": 101
}
```

Regras fixas:
- `item_type: manual`
- `severity: informational`
- `target_type: groups`
- `is_active: true`
- `is_indefinite: true`
- não enviar `ends_at` e `until_read` para manuais.

## Template de rastreio (`mural-sync.yml`)
Arquivo local: `docs/api-process-map/mural-sync.yml`

```yaml
environment: homolog  # homolog | prod — ambiente usado na última sync
project_name: TransportesAPI
root_external_id: FASTAPI_DOC__TransportesAPI__ROOT__manual
children:
  - external_id: FASTAPI_DOC__TransportesAPI__ENDPOINT__GET__clientes
    doc_kind: endpoint
    sort_order: 101
    mural_id: null
  - external_id: FASTAPI_DOC__TransportesAPI__PROCESSO__abertura_os
    doc_kind: process
    sort_order: 201
    mural_id: null
last_sync_at: null
```

## Regra obrigatória de anexos
- Nunca enviar arquivo binário direto para o Mural.
- Fluxo obrigatório:
  1. Upload do arquivo no Firebase Storage.
  2. Obter URL pública/interna acessível.
  3. Enviar no campo `attachments` do payload do Mural.
- Se não houver URL válida do Firebase, enviar `attachments: null`.

Exemplo:
```json
{
  "attachments": [
    {
      "file_name": "manual-endpoint-clientes.pdf",
      "file_url": "https://storage.googleapis.com/seu-bucket/fastapi-process-mapper/manual-endpoint-clientes.pdf",
      "file_extension": "pdf",
      "file_description": "Manual detalhado do endpoint GET /clientes"
    }
  ]
}
```

## Marcadores para preservar conteúdo manual
Usar sempre:

```html
<!-- FASTAPI_PROCESS_MAPPER:START -->
...conteúdo gerado pela skill...
<!-- FASTAPI_PROCESS_MAPPER:END -->
```

Ao atualizar:
- se marcadores existirem, substituir apenas o trecho entre eles;
- se não existirem, não sobrescrever todo o conteúdo automaticamente;
- preservar conteúdo manual fora dos marcadores.

## Regras de renderização HTML
- Mermaid deve ter quebra de linha real (não usar `\n` literal).
- links externos devem usar `target="_blank"` e `rel="noopener noreferrer"`.

Exemplo de link:
```html
<a href="https://exemplo.local/docs" target="_blank" rel="noopener noreferrer">Abrir documentação</a>
```

Exemplo de Mermaid:
```html
<pre><code class="language-mermaid">sequenceDiagram
participant A as App
participant API as FastAPI
A->>API: GET /clientes
API-->>A: 200 OK
</code></pre>
```

## Tratamento de erros HTTP
- `404`: pai inexistente -> criar ou upsert do raiz antes dos filhos.
- `409`: conflito de `external_id` ou reorder inconsistente -> parar e reportar.
- `422`: payload inválido -> corrigir campos obrigatórios e reenviar.

## Segurança antes de publicar
Remover ou mascarar:
- tokens, senhas, chaves de API;
- strings de conexão;
- IPs internos;
- URLs administrativas;
- dados pessoais sensíveis;
- segredos de `.env`.

Exemplos:
- `Authorization: Bearer abc` -> `Authorization: Bearer <token>`
- `192.168.0.10` -> `[IP interno removido]`
- `postgresql://user:pass@host/db` -> `<connection string removida>`

## Checklist pré-publicação
- raiz do projeto existente ou planejada;
- `summary` preenchido;
- `external_id` e `doc_kind` corretos;
- `status`, `doc_version`, `source` e `sort_order` definidos;
- parent de subitens via `parent_external_id` quando aplicável;
- conteúdo sensível removido;
- estratégia de upsert aplicada;
- `docs/api-process-map/mural-sync.yml` atualizado.
