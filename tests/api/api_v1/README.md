# Pasta `tests/api/api_v1/`

Esta pasta contém testes dos endpoints da versão `/api/v1`.

## Estrutura recomendada

```text
tests/api/api_v1/
└── endpoints/
    └── test_cars_endpoint.py
```

## Responsabilidade

Separar testes por versão da API.
Quando existir `/api/v2`, crie uma pasta separada:

```text
tests/api/api_v2/
```

## Regras principais

1. Mantenha testes da v1 isolados da v2.
2. Não quebre testes antigos ao criar nova versão.
3. Use nomes de arquivos próximos aos endpoints reais.
4. Teste compatibilidade de resposta quando a API for versionada.
