# Pasta `services/`

A pasta `services/` concentra regras de negócio da aplicação.
Ela fica entre os endpoints e o CRUD.

## Fluxo recomendado

```text
Endpoint -> Service -> CRUD -> Banco
Endpoint -> Service -> Core Client -> API externa
```

## Responsabilidade

Use services para:

- validar duplicidade;
- normalizar dados antes de salvar;
- controlar transição de status;
- bloquear ações inválidas;
- combinar consultas de múltiplos CRUDs;
- chamar APIs externas por meio de clients do `core`;
- montar payloads de integração;
- aplicar regras de negócio do domínio.

## Estrutura comum

```text
services/
├── __init__.py
├── base_service.py
├── car_service.py
├── service_order_service.py
└── external_status_service.py
```

## Exemplo

```python
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_cars import crud_car
from schemas.car_schema import CarCreate


class CarService:
    async def create_car(self, db: AsyncSession, payload: CarCreate):
        payload.name = payload.name.strip().upper()

        existing = await crud_car.get_by_plate(db=db, plate=payload.plate)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Já existe um carro com essa placa.",
            )

        return await crud_car.create(db=db, obj_in=payload)


car_service = CarService()
```

## Regras principais

1. Endpoint não deve ter regra grande; service deve ter.
2. CRUD não deve levantar erro HTTP; service pode levantar.
3. Services devem receber `db` como parâmetro quando usarem banco.
4. Services devem usar schemas como entrada quando possível.
5. Evite instanciar clients externos dentro de cada método repetidamente.
6. Padronize mensagens de erro.
7. Mantenha um service por domínio principal.
