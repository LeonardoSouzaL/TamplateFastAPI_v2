# Pasta `tests/`

A pasta `tests/` contém os testes automatizados do projeto.
Ela deve seguir a mesma separação de camadas da aplicação.

## Estrutura recomendada

```text
tests/
├── __init__.py
├── conftest.py
├── services/
│   └── test_car_service.py
└── api/
    └── api_v1/
        └── endpoints/
            └── test_cars_endpoint.py
```

## Responsabilidade

Use essa pasta para testar:

- services;
- endpoints;
- regras de negócio;
- validações;
- integrações mockadas;
- comportamento esperado em erros.

## Dependências comuns

```bash
pip install pytest pytest-asyncio httpx
```

## Como rodar

Rodar todos os testes:

```bash
pytest -v
```

Rodar apenas testes de services:

```bash
pytest tests/services -v
```

Rodar apenas testes de endpoints:

```bash
pytest tests/api -v
```

## Regras principais

1. Teste service separado de endpoint.
2. Use mocks para banco quando o foco for regra de negócio.
3. Use `httpx.AsyncClient` para testar endpoints assíncronos.
4. Evite depender de banco real nos testes unitários.
5. Nomeie arquivos com prefixo `test_`.
6. Nomeie funções com prefixo `test_`.
