# Pasta `api/api_v1/`

A pasta `api/api_v1/` representa a versão 1 da API.
Ela centraliza o roteamento dos endpoints versionados.

## Estrutura esperada

```text
api/api_v1/
├── __init__.py
├── api.py
└── endpoints/
```

## Responsabilidade

Esta pasta deve organizar tudo que pertence à versão `/api/v1`.
Quando uma nova versão da API for criada, como `/api/v2`, uma nova pasta deve seguir o mesmo padrão.

## Arquivo `api.py`

O arquivo `api.py` é o centralizador das rotas.
Sempre que um novo endpoint for criado em `endpoints/`, ele deve ser registrado aqui.

Exemplo:

```python
from fastapi import APIRouter

from api.api_v1.endpoints import cars

api_router = APIRouter()

api_router.include_router(
    cars.router,
    prefix="/cars",
    tags=["Cars"],
)
```

## Regras principais

1. Não coloque endpoints diretamente no `api.py`.
2. Use o `api.py` apenas para registrar rotas.
3. Mantenha prefixes claros, como `/cars`, `/service-orders`, `/users`.
4. Use tags para organizar a documentação Swagger.
5. Ao criar `/api/v2`, copie o padrão e não quebre a versão anterior.
