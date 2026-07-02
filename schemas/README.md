# Pasta `schemas/`

A pasta `schemas/` contém os schemas Pydantic usados para entrada e saída de dados da API.

## Estrutura comum

```text
schemas/
├── __init__.py
└── car_schema.py
```

## Responsabilidade

Os schemas devem:

- validar payloads de entrada;
- definir campos obrigatórios e opcionais;
- controlar o formato da resposta;
- documentar automaticamente a API no Swagger;
- separar criação, atualização e retorno.

## Padrão recomendado

```python
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CarBase(BaseModel):
    name: Optional[str] = None
    plate: Optional[str] = None
    is_active: Optional[bool] = True


class CarCreate(CarBase):
    name: str


class CarUpdate(CarBase):
    pass


class CarInDbBase(CarBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
```

## Regras principais

1. Use `Base` para campos comuns.
2. Use `Create` para payload de criação.
3. Use `Update` para payload de alteração.
4. Use `Response`, `InDB` ou `InDbBase` para retorno.
5. No Pydantic v2, use `ConfigDict(from_attributes=True)` para retorno com SQLAlchemy.
6. Não coloque consulta de banco dentro de schema.
7. Não coloque regra de negócio complexa aqui.

## Quando criar schemas separados

Crie schemas separados quando a resposta pública não deve expor todos os campos do banco.

Exemplo:

```text
UserCreate    -> recebe senha
UserResponse  -> nunca retorna senha
```
