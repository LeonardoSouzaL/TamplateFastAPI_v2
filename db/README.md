# Pasta `db/`

A pasta `db/` centraliza a configuração do banco de dados e a base do SQLAlchemy.

## Estrutura comum

```text
db/
├── __init__.py
├── base.py
├── base_class.py
└── session.py
```

## Responsabilidade

Esta pasta deve cuidar de:

- criação da base declarativa do SQLAlchemy;
- criação da engine;
- criação da sessão do banco;
- importação dos models para migrations e metadata;
- configuração de conexão com o banco.

## Arquivo `base_class.py`

Define a classe base dos models.

Exemplo:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

## Arquivo `base.py`

Importa todos os models para que o SQLAlchemy/Alembic reconheça as tabelas.

Exemplo:

```python
from db.base_class import Base
from models.car_model import Car
```

Sempre que criar um novo model, importe ele aqui.

## Arquivo `session.py`

Cria a engine e o sessionmaker.

Exemplo assíncrono:

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from core.config import settings

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
```

## Regras principais

1. Não coloque regra de negócio em `db/`.
2. Não crie sessão manualmente dentro dos endpoints.
3. Use `api/deps.py` para injetar sessão com `Depends`.
4. Importe todo novo model em `db/base.py`.
5. Mantenha a URI do banco em variável de ambiente.
