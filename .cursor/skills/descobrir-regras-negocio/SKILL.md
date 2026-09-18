---
name: descobrir-regras-negocio
description: Analisa projeto FastAPI existente para descobrir regras de negócio e propor rules 2xx-business. Use ao mapear projeto legado, antes de criar endpoints em domínios complexos ou quando uma regra nova for identificada durante desenvolvimento.
---

# Descobrir regras de negócio

## Objetivo

Analisar o diretório do projeto, identificar padrões reais de negócio e transformá-los em rules `.mdc` em `.cursor/rules/2xx-business-<dominio>-auto.mdc`.

Não substitui rules de arquitetura (000–070). Complementa com regras de domínio.

## Quando usar

- Projeto com módulos já implementados
- Regras espalhadas em endpoints/services/cruds
- Novos endpoints devem respeitar regras existentes
- Regra nova descoberta ou definida com o usuário

## Arquivos prioritários

```text
api/api_v1/endpoints/
services/
crud/
models/
schemas/
core/
tests/
README.md
.env.example
```

## O que procurar

Fluxos principais, validações, transições de status, permissões, normalizações, integrações obrigatórias, eventos/auditoria, cancelamentos, campos imutáveis, erros HTTP esperados, efeitos colaterais.

## Classificação (não inventar)

```text
Confirmada pelo código
Confirmada pelo README/documentação
Inferida com baixa confiança
Pergunta para o usuário
```

Rules novas **só** para regras confirmadas.

## Perguntas ao usuário (exemplos)

1. Status FINALIZADA exige histórico obrigatório?
2. Algum status bloqueia edição/exclusão?
3. Quais grupos podem criar/editar/cancelar?
4. Campos com normalização obrigatória (upper, strip)?
5. Endpoint dispara integração externa?
6. Cliente/projeto com regra especial?
7. Erros 400/403/404/409 por contexto?

## `.cursor/business-rules/` (auxiliar)

- `discovered-rules.md` — rascunhos
- `pending-questions.md` — lacunas
- `decisions.md` — decisões confirmadas

Rules ativas ficam em `.cursor/rules/*.mdc`.

## Criar rule de negócio

Nome: `.cursor/rules/2xx-business-<dominio>-auto.mdc`

Globs por domínio, ex.:

```yaml
globs: "{api/api_v1/endpoints/*service_order*.py,services/*service_order*.py,...}"
alwaysApply: false
```

Conteúdo mínimo: Escopo, Regras obrigatórias, Fluxos, Permissões, Status, Validações, Integrações, Erros esperados, Testes, Fonte.

## Critérios para virar rule

- Aplicável em mais de um endpoint
- Protege regra importante / evita regressão
- Impacta permissão, status, integração, financeiro, auditoria

## Saída da análise

1. Módulos encontrados
2. Regras confirmadas
3. Regras inferidas (pendentes)
4. Perguntas
5. Rules sugeridas (nomes `.mdc`)
6. Próximos passos

**Não alterar endpoints sem autorização explícita** — primeiro análise e composição de rules.

## Documentação após criar rule

- Atualizar `docs/cursor/rules-index.md`
- Atualizar `.cursor/business-rules/` se aplicável
- README do projeto + **Alterações recentes**
