---
name: executar-tarefa-template-fastapi
description: Executa tarefas maiores no template FastAPI seguindo camadas Endpoint-Service-CRUD e entrega estruturada. Use ao criar módulos, refatorar endpoints, alterar models/schemas ou concluir features multi-arquivo no projeto.
---

# Executar tarefa no template FastAPI

Antes de alterar código, identifique camadas impactadas: `api/`, `services/`, `crud/`, `models/`, `schemas/`, `core/`, `tests/`, `docs/`.

## Criar novo módulo

0. Garantir `db/session.py` + `api/deps.py` (rule `015-db-session-auto.mdc` / templates `docs/cursor/templates/db/`) se ainda não existirem
1. Model (se tabela nova)
2. Schemas (Base, Create, Update, Response)
3. CRUD
4. Service com regra de negócio
5. Endpoint chamando service
6. Registrar rota no router
7. Testes básicos
8. README + **Alterações recentes** se relevante

## Alterar endpoint existente

1. Verificar regra de negócio no endpoint
2. Mover para service se necessário
3. Manter endpoint leve
4. Ajustar testes da rota
5. Atualizar docs se mudar contrato

## Alterar model/schema

1. Impacto em CRUD, service, endpoint
2. Ajustar Create, Update, Response
3. Campos sensíveis fora do Response
4. Atualizar testes
5. README se mudar contrato

## Regras transversais

- Endpoint leve → service com negócio → CRUD só banco
- Sessão async: `DbDep` em endpoints; `get_db` sem auto-commit (rules 015 + 045)
- Não versionar secrets
- Testes: AsyncMock em unitários; sem API/banco real
- Regras de domínio: consultar `.cursor/rules/2xx-business-*`
- Abstrações reutilizáveis: avaliar `core/` (rule 115 / `docs/cursor/core-abstractions.md`)

## Saída ao finalizar

Explicar:

- arquivos criados, alterados, removidos
- regras/skills aplicadas
- comandos de teste recomendados
- pendências reais

Quando o usuário pedir ajuste em arquivo existente, entregar o **arquivo completo** corrigido.
