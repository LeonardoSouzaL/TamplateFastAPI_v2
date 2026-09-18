# Pasta `crud/`

A pasta `crud/` concentra o acesso ao banco de dados.
Ela deve conter classes e funções responsáveis por consultar, criar, atualizar e remover registros.

## Estrutura comum

```text
crud/
├── __init__.py
├── baseAsync.py
├── baseSync.py
├── crud_cars.py
├── crud_lastmile_metrics.py
├── crud_lastmile_os_metrics.py
├── crud_lastmile_os_pa_metrics.py
├── crud_lastmile_os_client_metrics.py
├── crud_lastmile_os_driver_metrics.py
├── crud_lastmile_os_overview_metrics.py
├── lastmile_os_sla.py
└── crud_lastmile_driver_metrics.py
```

`crud_lastmile_metrics.py` só agrega (`GROUP BY`, `COUNT FILTER`, lookup GAI). Sem `create`/`update`/`remove`. `crud_lastmile_driver_metrics.py` agrega viagens do dia por técnico/status e SLA. `lastmile_os_sla.py` concentra viagem atual e expressões de SLA reutilizadas por `by-pa`, `by-client`, `by-driver` e `overview`.

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
