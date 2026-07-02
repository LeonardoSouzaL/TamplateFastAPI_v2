# Pasta `models/`

A pasta `models/` contém os models SQLAlchemy da aplicação.
Cada model representa uma tabela do banco de dados.

## Estrutura comum

```text
models/
├── __init__.py
└── car_model.py
```

## Responsabilidade

Os models devem:

- definir tabelas;
- definir colunas;
- definir tipos de dados;
- definir chaves primárias e estrangeiras;
- definir relacionamentos entre tabelas;
- definir índices importantes.

## Exemplo

```python
from sqlalchemy import Boolean, Column, Integer, String
from db.base_class import Base


class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    plate = Column(String, nullable=True, index=True)
    is_active = Column(Boolean, default=True)
```

## O que não deve ficar no model

Evite colocar:

- regra de negócio;
- chamada de API externa;
- validação de payload;
- lógica HTTP;
- lógica de service.

## Regras principais

1. Um arquivo por domínio ou tabela principal.
2. Use nomes claros, como `car_model.py`, `user_model.py`, `service_order_model.py`.
3. Sempre herde de `Base`.
4. Sempre defina `__tablename__`.
5. Use `nullable=False` em campos obrigatórios.
6. Use `index=True` em campos muito consultados.
7. Após criar um model, importe-o em `db/base.py`.
