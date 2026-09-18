---
name: auditar-rules-skills-docs
description: Audita a organização de Cursor Rules, Skills e documentação em projetos FastAPI template. Use quando reorganizar rules, reduzir contexto global, migrar workflows para Skills ou validar links órfãos entre .cursor/rules, .cursor/skills e docs/cursor.
---

# Auditar Rules, Skills e Docs

## Objetivo

Mapear duplicação, rules gigantes, referências órfãs e oportunidades de enxugar contexto global sem quebrar comportamento do agente.

## Checklist de auditoria

```text
- [ ] Listar .cursor/rules/*.mdc (alwaysApply vs globs)
- [ ] Identificar duplicação entre 000, 010 e .cursorrules
- [ ] Rules >150 linhas candidatas a Skill + stub
- [ ] Rules manual (085, 100, 120) — já têm Skill?
- [ ] Rule gate 005-rule-vs-skill-gate-always.mdc existe?
- [ ] Referências a .cursor/rules/README.md (deve ser docs/cursor/rules-index.md)
- [ ] Links em AGENTS.md, .cursorrules, docs/cursor/*
- [ ] Skills em .cursor/skills/ (não em skills-cursor)
- [ ] Rules 200–280 intactas (negócio não vira Skill)
- [ ] docs/observability, docs/cursor/templates atualizados
- [ ] Rule 015 (sessão async) alinhada com 020, 045 e templates db/
- [ ] Endpoints usam DbDep; get_db sem auto-commit quando CRUD commita
- [ ] Rule 045 referencia Skill `migrar-transacao-crud-fastapi` (plano/migração)
```

## Classificação por tipo

| Tipo | Onde fica | Exemplo |
|------|-----------|---------|
| Princípio global curto | rule `alwaysApply: true` | 000, 005, 080, 333 stub |
| Padrão por camada | rule com globs | 020–070 |
| Workflow longo | Skill + rule stub | 085, OTEL |
| Negócio confirmado | rule 2xx | 210-tracking |
| Índice/documentação | docs/cursor/ | rules-index.md |

## Gate Rule vs Skill

O projeto deve ter a rule global `005-rule-vs-skill-gate-always.mdc` (`alwaysApply: true`). Ela orienta o agente a **questionar o usuário** antes de criar uma rule quando o pedido na verdade deveria ser Skill.

**Critérios para questionar (mesmos da auditoria):**

- Passo a passo reutilizável → Skill
- Rotina com etapas → Skill
- Muito grande para rule → Skill
- Só precisa quando solicitado → Skill
- Regra fixa global curta → Rule

**Ao final de cada auditoria** (ou ao detectar pedido de nova rule grande/operacional):

1. Verificar se `005-rule-vs-skill-gate-always.mdc` existe em `.cursor/rules/`.
2. Se não existir, propor ou criar a rule gate.
3. Se o usuário pediu criar rule e o conteúdo é workflow, sugerir Skill e aguardar confirmação.

## Saída esperada

1. Tabela: arquivo | linhas | ação (manter/encurtar/skill/docs)
2. Links órfãos encontrados
3. Plano em fases (quick wins → skills → enxugar → entry points)
4. Lista de arquivos a criar/mover/renomear

## Regras da refatoração

- Não remover instruções críticas sem destino (Skill ou docs).
- Stubs manuais: "Use a Skill X quando..."
- Manter rules de negócio 200–280 em `.cursor/rules/`.
- Atualizar README do projeto (Alterações recentes) após mudanças relevantes.

## Validação pós-refatoração

```text
grep -r "rules/README" .
grep -r "333-cursor_rule" .
# Confirmar docs/cursor/rules-index.md existe
# Confirmar .cursor/skills/*/SKILL.md existem
# Confirmar 005-rule-vs-skill-gate-always.mdc existe
```
