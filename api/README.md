# Pasta `api/`

A pasta `api/` concentra a camada HTTP da aplicação FastAPI.
Ela deve conter apenas rotas, dependências e versionamento da API.

## Estrutura esperada

```text
api/
├── __init__.py
├── deps.py
└── api_v1/
    ├── __init__.py
    ├── api.py
    └── endpoints/
```

## Responsabilidade

A camada `api` deve:

- receber requisições HTTP;
- validar payloads usando schemas Pydantic;
- injetar dependências, como sessão de banco, usuário autenticado ou API key;
- chamar `services`, `core` ou `crud`;
- retornar respostas padronizadas.

## O que não deve ficar aqui

Evite colocar dentro dos endpoints:

- regra de negócio longa;
- consulta complexa ao banco;
- integração direta com APIs externas usando `httpx`;
- montagem manual de payloads complexos;
- regras de status, validação de duplicidade ou transição de fluxo.

Para isso, use `services/` ou `core/`.

## Regras principais

1. Cada arquivo de endpoint deve representar um domínio.
2. Não misture muitos recursos diferentes no mesmo arquivo.
3. Sempre use `response_model` quando possível.
4. Sempre use schemas para entrada e saída.
5. Sempre registre as rotas versionadas em `api/api_v1/api.py`.

## Exemplo básico

```python
from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api import deps
from schemas.car_schema import CarCreate, CarInDbBase
from services.car_service import car_service

router = APIRouter()


@router.post("/", response_model=CarInDbBase)
async def create_car(
    *,
    db: AsyncSession = Depends(deps.get_db),
    payload: CarCreate,
) -> Any:
    return await car_service.create_car(db=db, payload=payload)
```
