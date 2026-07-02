# Pasta `api/api_v1/endpoints/`

Esta pasta contém os endpoints da versão 1 da API.
Cada arquivo deve representar um recurso ou domínio da aplicação.

## Exemplos de arquivos

```text
endpoints/
├── cars.py
├── service_orders.py
├── travels.py
├── clients.py
└── tracking.py
```

## Responsabilidade dos endpoints

Um endpoint deve:

- receber a requisição;
- validar parâmetros e payloads;
- obter dependências com `Depends`;
- chamar a camada correta, geralmente `services/`;
- retornar o resultado com `response_model`.

## Padrão recomendado

```python
@router.post("/", response_model=CarInDbBase)
async def create_car(
    *,
    db: AsyncSession = Depends(deps.get_db),
    payload: CarCreate,
) -> Any:
    return await car_service.create_car(db=db, payload=payload)
```

## Regras principais

1. Não coloque regra de negócio pesada no endpoint.
2. Não acesse API externa diretamente no endpoint.
3. Não monte query SQL complexa diretamente no endpoint.
4. Use nomes claros para rotas e funções.
5. Use `Query`, `Path` e `Body` quando precisar documentar validações.
6. Prefira `services` para regras e `crud` para banco.

## Fluxo recomendado

```text
Endpoint -> Service -> CRUD -> Banco
Endpoint -> Service -> Core Client -> API externa
```

## Exemplo com paginação

```python
@router.get("/", response_model=list[CarInDbBase])
async def list_cars(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await car_service.list_cars(
        db=db,
        skip=skip,
        limit=limit,
    )
```
