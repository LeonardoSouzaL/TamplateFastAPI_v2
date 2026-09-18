# Business Rules do projeto

Esta pasta é opcional e serve para organizar **documentação de apoio** sobre regras de negócio descobertas em projetos já em andamento.

> Importante: esta pasta **não substitui** `.cursor/rules/`.

As rules que o Cursor deve carregar como instrução ativa continuam sendo arquivos `.mdc` dentro de:

```text
.cursor/rules/
```

Use esta pasta para guardar materiais auxiliares, como:

```text
.cursor/business-rules/
├── README.md
├── discovered-rules.md
├── pending-questions.md
└── decisions.md
```

## Papel desta pasta

Esta pasta ajuda o time a registrar:

- regras de negócio identificadas durante análise do projeto;
- perguntas pendentes para o usuário ou área de negócio;
- decisões tomadas durante uma implementação;
- regras candidatas a virar `.mdc`;
- histórico de descobertas relevantes por domínio.

## O que deve virar `.mdc`

Quando uma regra for confirmada e precisar orientar futuras alterações de código, ela deve virar uma rule ativa em:

```text
.cursor/rules/2xx-business-<dominio>-auto.mdc
```

Rules já criadas neste projeto:

```text
.cursor/rules/200-business-movements-auto.mdc
.cursor/rules/210-business-romaneios-auto.mdc
.cursor/rules/215-business-transport-integration-auto.mdc
.cursor/rules/220-business-cielo-sap-auto.mdc
.cursor/rules/230-business-catalog-auto.mdc
.cursor/rules/240-technician-bag-auth-app-location.mdc
.cursor/rules/250-business-claro-indoor-auto.mdc
.cursor/rules/260-business-supply-control-auto.mdc
```

## O que pode ficar apenas aqui

Pode ficar apenas nesta pasta quando for:

- anotação de análise;
- hipótese ainda não confirmada;
- pergunta pendente;
- decisão temporária;
- documentação de apoio que não precisa ser carregada pelo Cursor em toda tarefa.

Decisões de **2026-06-01** (REVERSA vs RETURN, finish com `status_rom` real, auth, catálogo origens) estão aplicadas nas rules ativas `200`–`230` em `.cursor/rules/`.

## Fluxo recomendado

1. Use a Skill `descobrir-regras-negocio` ou a rule `120-business-rules-discovery-manual.mdc`.
2. Peça para o Cursor analisar o projeto atual.
3. Registre hipóteses e dúvidas nesta pasta, se necessário.
4. Confirme as regras com o usuário/time.
5. Transforme regras confirmadas em `.mdc` dentro de `.cursor/rules/`.
6. Atualize `docs/cursor/rules-index.md` com a nova rule criada.
7. Atualize o README do projeto e a seção `Alterações recentes`, quando aplicável.

## Regra principal

```text
Documentação auxiliar pode ficar em .cursor/business-rules/.
Rules ativas devem continuar em .cursor/rules/.
```
