---
name: fastapi-process-mapper
description: Mapeia projetos FastAPI, identifica endpoints, relaciona rotas com processos da empresa e organiza documentação técnica/funcional com matriz de impacto e diagramas. Use quando o usuário pedir mapeamento de API, catálogo de endpoints, melhoria de Swagger/OpenAPI, descoberta de consumidores/dependências ou documentação para onboarding e manutenção.
disable-model-invocation: true
---

# FastAPI Process Mapper

## Objetivo
Transformar APIs FastAPI em documentação técnica e funcional navegável, segura e útil para manutenção, onboarding e análise de impacto.

## Quando usar
Use esta skill quando o usuário pedir para:
- mapear endpoints de uma API FastAPI;
- documentar rotas por endpoint e por processo;
- melhorar Swagger/OpenAPI;
- descobrir dependências, consumidores e impacto de alterações;
- gerar base de conhecimento para novos desenvolvedores.

## Princípios obrigatórios
- Responder sempre em PT-BR.
- Trabalhar por padrão em leitura e análise (`MODO_ANALISAR`).
- Não alterar código de produção sem pedido explícito de modo de aplicação.
- Não inventar processo, consumidor, dependência, criticidade ou regra de negócio.
- Quando faltar confirmação, usar `pendente_validacao_usuario`.
- Marcar origem da informação com: `detectado_no_codigo`, `inferido_pelo_agente`, `confirmado_pelo_usuario`, `pendente_validacao_usuario`.
- Respeitar `.cursor/rules/`, `AGENTS.md` e padrões do projeto.
- Em caso de conflito com Rule, avisar o usuário antes de prosseguir.
- Nunca expor segredos, tokens, senhas, conexão de banco ou infraestrutura sensível.
- Para diagramas, priorizar Mermaid com quebras reais de linha (nunca `\n` literal no conteúdo final).
- Em links externos no HTML publicado, usar `target="_blank"` e `rel="noopener noreferrer"`.
- Quando publicar no Mural, respeitar hierarquia e governança: 1 item raiz (`doc_kind: overview`) por projeto e subitens com `doc_kind`, `status` e `sort_order`.

## Fluxo padrão resumido
1. Descobrir endpoints e contexto técnico (routers, includes, schemas, services, integrações).
2. Montar catálogo estruturado (`endpoint-catalog.yml`).
3. Agrupar por domínio e conduzir entrevista funcional em lotes pequenos.
4. Produzir documentação por endpoint, processo, matriz de impacto e pendências.
5. Propor melhorias de Swagger/OpenAPI e schemas sem alterar contrato sem validação.
6. Validar completude, riscos, criticidade e consistência entre fontes.
7. Quando houver Mural: executar bootstrap (`MODO_MURAL_BOOTSTRAP_ENV`) — pergunta única: **homolog ou prod?**
8. Opcional: sincronizar publicação no Mural interno com hierarquia (`1 raiz + subitens por tópico`) e `external_id` estável.

## Bootstrap do Mural (sem `.env`)
Antes de qualquer operação em `MODO_MURAL_PUBLICAR`, `MODO_MURAL_ATUALIZAR` ou `MODO_MURAL_SYNC`:

1. Ler presets em [mural-presets.yml](mural-presets.yml) — **não exige** variáveis de ambiente.
2. Se o usuário não informou o ambiente, perguntar apenas: **homolog ou prod?**
3. Resolver `api_base_url`, `target_group_id` e `created_by_id` do preset escolhido.
4. Em **prod**, exigir confirmação explícita adicional antes do primeiro upsert.
5. Só pedir `MURAL_API_TOKEN` se `requires_token: true` no preset (hoje `false` nos dois ambientes).
6. Override manual (URL, grupo ou `created_by_id`) **somente** se o usuário pedir explicitamente.

Presets embutidos (fonte: `mural-presets.yml`):

| Ambiente | `api_base_url` | `target_group_id` | `created_by_id` |
|----------|----------------|-------------------|-----------------|
| homolog | `https://192.168.0.214/hg-api-mural/api/v1/items` | `34` | `122` |
| prod | `http://192.168.0.215/api-mural/api/v1/items` | `323` | `1037` |

Regras de separação:
- nunca misturar preset de homolog com prod na mesma execução;
- se o usuário já disse o ambiente na mensagem, não perguntar de novo;
- ambiente padrão quando não informado: `homolog` (mas confirmar antes de publicar).

Saída esperada do bootstrap:
- ambiente resolvido (`homolog` ou `prod`);
- preset aplicado (`ok`);
- decisão: `apto_para_publicacao` ou `bloqueado_por_config` (só se override inválido ou prod sem confirmação).

## Estrutura de saída esperada
- `docs/api-process-map/endpoint-catalog.yml`
- `docs/api-process-map/endpoints/*.md`
- `docs/api-process-map/processos/*.md`
- `docs/api-process-map/matriz-impacto.md`
- `docs/api-process-map/pendencias.md`
- `docs/api-process-map/reports/status-documentacao.md`
- `docs/api-process-map/mural-sync.yml` (quando houver Mural)

## Regras de alteração de código
- `MODO_SWAGGER_PROPOR`: apenas proposta; não edita arquivos.
- `MODO_SWAGGER_APLICAR`: pode editar decorators/schemas somente após resumo de impacto e confirmação.
- Nunca alterar regras de negócio, queries, autenticação, contratos e rotas sem aprovação explícita.
- Se houver risco para `operation_id` usado externamente, parar e pedir validação do usuário.

## OpenAPI — exemplos e campos obrigatórios (Pydantic v2)
- Não substituir o exemplo auto-gerado pelo Pydantic/FastAPI por payload mínimo em `json_schema_extra.examples` ou `Field(examples=...)` no model raiz do request/response.
- Preferir o exemplo gerado pelo schema (todos os campos visíveis no Swagger, incluindo opcionais).
- Só usar `json_schema_extra.examples` quando o exemplo for **completo e realista** (todos os campos do model), nunca reduzido ou "slim".
- Sinalizar obrigatoriedade via tipo sem `Optional` + `Field(..., description="(obrigatório)")`, conferindo o uso real no handler/service antes de alterar o schema.
- Não confundir documentação com contrato: tornar campo obrigatório no Pydantic altera validação em runtime — exigir aprovação explícita.
- Anti-padrão: exemplos "slim" copiados de testes unitários ou fixtures mínimas que escondem campos opcionais que integradores precisam ver.

## Referências detalhadas
- Modos e prompts: [modos-e-prompts.md](modos-e-prompts.md)
- Templates de documentação: [templates-documentacao.md](templates-documentacao.md)
- Presets Mural (homolog/prod): [mural-presets.yml](mural-presets.yml)
- Sync com Mural interno: [mural-sync.md](mural-sync.md)
