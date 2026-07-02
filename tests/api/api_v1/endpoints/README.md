# Pasta `tests/api/api_v1/endpoints/`

Esta pasta contém os testes dos arquivos em `api/api_v1/endpoints/`.

## Padrão de nome

```text
api/api_v1/endpoints/cars.py
```

Deve ter um teste correspondente:

```text
tests/api/api_v1/endpoints/test_cars_endpoint.py
```

## Exemplo

```python
import pytest


@pytest.mark.asyncio
async def test_list_cars_deve_retornar_200(async_client):
    response = await async_client.get("/api/v1/cars/")

    assert response.status_code == 200
```

## Regras principais

1. Um arquivo de teste por endpoint principal.
2. Valide status code.
3. Valide estrutura do JSON.
4. Mocke services quando necessário.
5. Teste cenários de sucesso e erro.
6. Teste query params e path params relevantes.
