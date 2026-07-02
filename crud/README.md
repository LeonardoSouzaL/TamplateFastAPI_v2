# Pasta `crud/`

A pasta `crud/` concentra o acesso ao banco de dados.
Ela deve conter classes e funções responsáveis por consultar, criar, atualizar e remover registros.

## Estrutura comum

```text
crud/
├── __init__.py
├── baseAsync.py
├── baseSync.py
└── crud_cars.py
```

## Responsabilidade

O CRUD deve:

- executar consultas no banco;
- aplicar filtros;
- ordenar resultados;
- paginar consultas;
- criar, atualizar e remover registros;
- centralizar métodos específicos de consulta por domínio.

## O que não deve ficar aqui

Evite colocar no CRUD:

- regra de negócio complexa;
- validações de fluxo;
- chamadas para APIs externas;
- regras de permissão;
- montagem de respostas HTTP.

Esses pontos devem ficar em `services/` ou `api/`.

## Exemplo de CRUD específico

```python
from crud.baseAsync import CRUDBase
from models.car_model import Car
from schemas.car_schema import CarCreate, CarUpdate


class CRUDCar(CRUDBase[Car, CarCreate, CarUpdate]):
    async def get_by_plate(self, db, *, plate: str):
        return await self.get_last_by_filters(
            db=db,
            filters={
                "plate": {"operator": "==", "value": plate}
            },
        )


crud_car = CRUDCar(Car)
```

## Regras principais

1. Um arquivo CRUD para cada model principal.
2. Use `CRUDBase` sempre que possível.
3. Métodos específicos devem ser consultas, não regras de negócio.
4. Nunca retorne `HTTPException` dentro do CRUD.
5. O CRUD deve retornar objetos, listas ou `None`.
6. Tratamento HTTP deve ficar no endpoint ou service.

## Fluxo recomendado

```text
Service -> CRUD -> Banco
```
