# Metrics API

API FastAPI **somente leitura** que concentra métricas do sistema Arancia para os dashboards.

A primeira onda cobre o fluxo **LastMile** (mesmo contrato JSON da API de Transportes v2), calculando KPIs no PostgreSQL com `GROUP BY`/`COUNT FILTER` em vez de carregar viagens em memória.

```text
Endpoint -> Service -> CRUD (SQL agregado, read-only) -> PostgreSQL Transportes
```

Copie `core/example-config.py` para `core/config.py` e preencha host/usuário/senha fictícios locais. Não versionar secrets.

### Endpoints LastMile

- `GET /api/v1/lastmile/dashboard/pa-summary`
- `GET /api/v1/lastmile/dashboard/metrics?metric=pending|without_driver|finished|worst_late_pa`
- `GET /api/v1/lastmile/dashboard/driver-status-summary` — totais de **viagens** LastMile do dia por técnico/status e SLA (`created_at`, `designation_id`, `driver_id`, `carrier_id`, `cliente_id`)
- `GET /api/v1/lastmile/orders/by-status` — totais de **OS** da visão LastMile, com filtro opcional `status` (CSV), `finished` e `data_inicial`/`data_final` (`service_order.created_at`)
- `GET /api/v1/lastmile/orders/by-pa` — totais de **OS** LastMile agrupados por PA (`designacao`), com SLA, `pa_ofensora`/`ofensoras` e `melhor_pa`/`melhores`
- `GET /api/v1/lastmile/orders/by-client` — totais de **OS** LastMile agrupados por cliente (`cliente`), com SLA, `cliente_ofensor`/`ofensores` e `melhor_cliente`/`melhores`
- `GET /api/v1/lastmile/orders/by-driver` — totais de **OS** LastMile agrupados por técnico (`tecnico` / `auth_app.uid`), com SLA, ociosidade (`last_opening` + rota do dia) e rankings `tecnico_ofensor`/`melhor_tecnico`/`tecnico_ocioso`
- `GET /api/v1/lastmile/orders/overview` — visão geral de **OS** LastMile (pendente, atendida, prazo, sem técnico, percentuais e efetividade), com filtros de PA e cliente

Dashboards de viagem: sem `order_type`, filtra `LASTMILE,LASTMILE_COLLECT,LASTMILE_DELIVERY`. Datas em `coalesce(route_date, created_at)` são opcionais.

Totais de OS: sem `order_type`, usa `LASTMILE_OS_TYPE_PATTERNS` (`COLLECT`, `NORMAL`, `DESINSTAL%`, `RETIRADA%`). `status=PENDING` conta só `UPPER(type)='PENDING'`. Datas opcionais em `service_order.created_at`. Visão por PA usa a mesma visão de tipos e a PA da OS (`service_order.designation_id`). Visão por cliente usa a mesma visão de tipos e o cliente da OS (`service_order.client_id`). Visão por técnico usa a mesma visão de tipos e o `driver_id` da viagem atual (`auth_app.uid`); ociosidade exige rota hoje (`route_date`) e só conta após 50 minutos sem `last_opening`. Visão geral usa a mesma visão de tipos, PA da OS e cliente da OS, com totais planos (sem ranking).

## Alterações recentes

| Data | Tipo | Módulo/Pasta | Alteração | Impacto |
| ---- | ---- | ------------ | --------- | ------- |
| 2026-09-18 | Adicionado | `api/`, `services/`, `crud/`, `schemas/` | Endpoint novo `GET /lastmile/orders/overview` (visão geral de OS LastMile). | Cards de pendente/atendida/prazo/sem técnico, percentuais e efetividade, com filtro de PA e cliente, sem alterar os demais `/orders`. |
| 2026-09-18 | Alterado | `core/`, `services/`, `tests/` | Carência de ociosidade do técnico em `GET /lastmile/orders/by-driver` passou de 5 para 50 min. | 53 min parado → 180 s ocioso; até 50 min continua 0. |
| 2026-09-18 | Adicionado | `api/`, `services/`, `crud/`, `schemas/`, `models/` | Endpoint novo `GET /lastmile/orders/by-driver` (totais de OS LastMile por técnico/`auth_app`). | Visão LastMile da OS agrupada por técnico, com SLA, ociosidade e rankings, sem alterar `by-status` / `by-pa` / `by-client`. |
| 2026-09-18 | Adicionado | `api/`, `services/`, `crud/`, `schemas/` | Endpoint novo `GET /lastmile/orders/by-client` (totais de OS LastMile por cliente/GAI). | Visão LastMile da OS agrupada por cliente, com SLA e rankings, sem alterar `by-status` / `by-pa`. |
| 2026-09-17 | Adicionado | `api/`, `services/`, `crud/`, `schemas/`, `models/` | Endpoint `GET /lastmile/dashboard/driver-status-summary` (viagens LastMile do dia por técnico/status e SLA). | Totais por técnico sem hidratar viagem nem teto de 5000 da Transportes v1. |
| 2026-09-17 | Alterado | `schemas/`, `services/` | Rankings `pa_ofensora`, `ofensoras`, `melhor_pa` e `melhores` em `GET /lastmile/orders/by-pa`. | Cards de ofensoras/melhores no mesmo GET, sem consulta extra nem alteração de banco. |
| 2026-09-17 | Alterado | `schemas/`, `crud/`, `services/` | Removido `com_viagem_count` de `GET /lastmile/orders/by-pa`. | Status da viagem continua em `by_status_viagem`; sem alteração de banco. |
| 2026-09-17 | Adicionado | `api/`, `services/`, `crud/`, `schemas/`, `models/` | Endpoint `GET /lastmile/orders/by-pa` (totais de OS LastMile por PA/`designacao`). | Visão LastMile da OS agrupada por PA, com viagem atual, sem técnico e SLA de prazo. |
| 2026-09-17 | Alterado | `api/`, `services/`, `crud/`, `schemas/`, `models/` | Filtro `data_inicial`/`data_final` em `GET /lastmile/orders/by-status` sobre `service_order.created_at`. | Recorte de OS LastMile por período de criação, inclusive no `universe_total`. |
| 2026-09-17 | Adicionado | `api/`, `services/`, `crud/`, `schemas/`, `models/` | Endpoint `GET /lastmile/orders/by-status` (totais de OS LastMile por status/`finished`). | Visão LastMile da OS com PENDING puro e filtro de finalizador, separado dos KPIs de viagem. |
| 2026-09-16 | Adicionado | `api/`, `services/`, `crud/`, `models/`, `schemas/` | Dashboard LastMile somente leitura (`pa-summary` e `metrics`) com agregação SQL. | Front consome métricas sem passar pela API de Transportes. |
| 2026-09-16 | Adicionado | `core/` | Identidade MetricsAPI, OTEL/Loki, sessão PostgreSQL read-only. | Observabilidade e consultas sem escrita no banco. |
| 2026-09-16 | Removido | `api/api_v1/endpoints/cars.py` | Rotas de exemplo `cars` saíram do router (módulo permanece como exemplo). | API não expõe escrita do template. |

---

# Template FastAPI

Template base para criação de APIs em **FastAPI** seguindo um padrão modular, reutilizável e escalável para projetos com SQLAlchemy, Pydantic, CRUD abstrato, services, consumo de APIs externas, testes automatizados e rotas versionadas.

Template base para criação de APIs em **FastAPI** seguindo um padrão modular, reutilizável e escalável para projetos com SQLAlchemy, Pydantic, CRUD abstrato, services, consumo de APIs externas, testes automatizados e rotas versionadas.

Este projeto foi pensado para manter uma separação clara entre camadas:

```text
Endpoint -> Service -> CRUD -> Banco
Endpoint -> Service -> Core Client -> API externa
```

A documentação detalhada de cada pasta fica dentro do próprio `README.md` da respectiva pasta. Este arquivo principal serve como visão geral do projeto, guia rápido de instalação e referência para o fluxo recomendado.

---

## 1. Objetivo do template

Este template serve como ponto de partida para APIs FastAPI com:

- organização por módulos;
- rotas versionadas em `/api/v1`;
- conexão com banco usando SQLAlchemy;
- sessões assíncronas com `AsyncSession`;
- schemas Pydantic para entrada e saída de dados;
- CRUD abstrato reutilizável;
- camada de `services` para regra de negócio;
- consumo padronizado de APIs externas em `core`;
- suporte a OAuth2, API Key, Bearer Token, Basic Auth e certificado/mTLS;
- endpoints separados por responsabilidade;
- configuração centralizada;
- suporte a filtros dinâmicos;
- suporte a relacionamentos em consultas;
- suporte a paginação, ordenação e agregações;
- exemplos de testes automatizados;
- exemplos práticos de integração externa;
- facilidade para criação de novos módulos.

---

## 2. Estrutura geral do projeto

```text
TemplateFastAPI/
├── api/
│   ├── README.md
│   ├── deps.py
│   └── api_v1/
│       ├── README.md
│       ├── api.py
│       └── endpoints/
│           ├── README.md
│           └── cars.py
│
├── core/
│   ├── README.md
│   ├── example-config.py
│   ├── filters.py
│   ├── oauth2_client.py
│   ├── request.py
│   └── xml_render.py
│
├── crud/
│   ├── README.md
│   ├── baseAsync.py
│   ├── baseSync.py
│   └── crud_cars.py
│
├── db/
│   ├── README.md
│   ├── base.py
│   ├── base_class.py
│   └── session.py
│
├── models/
│   ├── README.md
│   └── car_model.py
│
├── schemas/
│   ├── README.md
│   └── car_schema.py
│
├── services/
│   ├── README.md
│   ├── base_service.py
│   ├── car_service.py
│   ├── external_status_service.py
│   └── service_order_service.py
│
├── tests/
│   ├── README.md
│   ├── conftest.py
│   ├── services/
│   │   ├── README.md
│   │   └── test_car_service.py
│   └── api/
│       ├── README.md
│       └── api_v1/
│           ├── README.md
│           └── endpoints/
│               ├── README.md
│               └── test_cars_endpoint.py
│
├── examples/
│   ├── README.md
│   └── oauth2_clients/
│       ├── README.md
│       ├── abbiamo_client_example.py
│       ├── mtls_client_example.py
│       └── oauth2_client_credentials_example.py
│
├── main.py
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## 3. Responsabilidade resumida das pastas

| Pasta | Responsabilidade | Documentação detalhada |
|---|---|---|
| `api/` | Camada HTTP, dependências e versionamento de rotas. | [`api/README.md`](api/README.md) |
| `api/api_v1/` | Registro das rotas da versão 1. | [`api/api_v1/README.md`](api/api_v1/README.md) |
| `api/api_v1/endpoints/` | Endpoints separados por domínio/recurso. | [`api/api_v1/endpoints/README.md`](api/api_v1/endpoints/README.md) |
| `core/` | Configurações, clients HTTP, OAuth2, helpers globais e integrações técnicas. | [`core/README.md`](core/README.md) |
| `crud/` | Acesso ao banco, queries, filtros, paginação e persistência. | [`crud/README.md`](crud/README.md) |
| `db/` | Engine, sessão, base SQLAlchemy e imports de models. | [`db/README.md`](db/README.md) |
| `models/` | Models SQLAlchemy que representam tabelas. | [`models/README.md`](models/README.md) |
| `schemas/` | Schemas Pydantic de entrada, atualização e resposta. | [`schemas/README.md`](schemas/README.md) |
| `services/` | Regras de negócio, validações, normalizações e orquestração entre CRUD/API externa. | [`services/README.md`](services/README.md) |
| `tests/` | Testes automatizados do projeto. | [`tests/README.md`](tests/README.md) |
| `examples/` | Exemplos práticos e não obrigatórios. | [`examples/README.md`](examples/README.md) |

---

## 4. Fluxo recomendado das camadas

### 4.1. Fluxo com banco de dados

```text
Endpoint -> Service -> CRUD -> Model/Banco
```

Exemplo:

```python
@router.post("/", response_model=CarInDbBase)
async def create_car(
    *,
    db: AsyncSession = Depends(deps.get_db),
    car_in: CarCreate,
) -> Any:
    return await car_service.create_car(
        db=db,
        payload=car_in,
    )
```

Nesse fluxo:

- `endpoint` recebe a requisição;
- `schema` valida o payload;
- `service` aplica regra de negócio;
- `crud` acessa o banco;
- `model` representa a tabela.

### 4.2. Fluxo com API externa

```text
Endpoint -> Service -> Core Client -> API externa
```

Exemplo:

```python
response = await external_status_service.send_status(
    payload={
        "order_number": "123",
        "status": "confirmed",
    }
)
```

A configuração do client externo fica centralizada em `core/`, especialmente quando envolver autenticação, token, certificado ou headers específicos.

---

## 5. Camada `services`

A pasta `services/` foi adicionada para separar regra de negócio dos endpoints.

Use `services/` para:

- validar duplicidade;
- normalizar campos;
- verificar status antes de alterar registros;
- orquestrar várias operações de CRUD;
- montar payloads para APIs externas;
- centralizar regras reutilizáveis;
- evitar endpoints grandes.

Exemplo:

```python
from services.car_service import car_service

car = await car_service.create_car(
    db=db,
    payload=car_in,
)
```

Mais detalhes em [`services/README.md`](services/README.md).

---

## 6. Consumo de APIs externas com OAuth2 e outras autenticações

Foi adicionado em `core/` um client reutilizável para APIs externas:

```text
core/oauth2_client.py
```

Ele suporta os principais cenários de autenticação:

- sem autenticação;
- API Key via header;
- API Key via query param;
- Bearer token fixo;
- Basic Auth;
- OAuth2 Client Credentials;
- OAuth2 Password Grant;
- client secret via Basic Auth;
- client secret no body;
- certificado/mTLS;
- CA bundle customizado;
- headers extras;
- cache automático de token;
- renovação automática do token quando expirar.

Exemplo com API Key:

```python
from core.oauth2_client import APIAuthConfig, AuthType, OAuth2APIClient

client = OAuth2APIClient(
    base_url="https://api.externa.com.br",
    auth_config=APIAuthConfig(
        auth_type=AuthType.API_KEY,
        api_key="sua-chave",
        api_key_name="x-api-key",
        api_key_location="header",
    ),
)

response = await client.request(
    "POST",
    "/v1/status",
    data={"status": "confirmed"},
)
```

Exemplos completos em [`examples/oauth2_clients/README.md`](examples/oauth2_clients/README.md).

---

## 7. Testes automatizados

Foi adicionada uma estrutura inicial de testes:

```text
tests/
├── conftest.py
├── services/
└── api/
```

A separação recomendada é:

- `tests/services/`: testa regra de negócio com mocks;
- `tests/api/`: testa comportamento dos endpoints;
- `tests/conftest.py`: concentra fixtures reutilizáveis.

Instale as dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

Execute todos os testes:

```bash
pytest -v
```

Execute apenas testes de services:

```bash
pytest tests/services -v
```

Execute apenas testes de endpoints:

```bash
pytest tests/api -v
```

Mais detalhes em [`tests/README.md`](tests/README.md).

---

## 8. Instalação do projeto

### 8.1. Criar ambiente virtual

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Linux:

```bash
python -m venv venv
source venv/bin/activate
```

### 8.2. Instalar dependências

```bash
pip install -r requirements.txt
```

Para testes:

```bash
pip install -r requirements-dev.txt
```

Recomendação: em projetos novos, usar Python 3.11 ou 3.12 para evitar conflitos com bibliotecas que ainda não suportam versões muito recentes.

---

## 9. Configuração do ambiente

Crie o arquivo `.env` na raiz do projeto:

```env
PROJECT_NAME=Template FastAPI
API_V1_STR=/api/v1
SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://usuario:senha@localhost:5432/minha_base
API_KEY=sua-chave-interna
BACKEND_CORS_ORIGINS=["*"]
```

Caso o projeto use `core/example-config.py`, copie para `core/config.py` e ajuste as variáveis conforme o ambiente.

Linux:

```bash
cp core/example-config.py core/config.py
```

Windows PowerShell:

```powershell
Copy-Item core/example-config.py core/config.py
```

Mais detalhes em [`core/README.md`](core/README.md).

---

## 10. Rodar o projeto localmente

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Acesse:

```text
http://127.0.0.1:8000/docs
```

ou:

```text
http://127.0.0.1:8000/redoc
```

---

## 11. Criando um novo módulo

Para criar um novo domínio, siga esta ordem:

```text
1. Criar model em models/
2. Importar model em db/base.py
3. Criar schemas em schemas/
4. Criar CRUD específico em crud/
5. Criar service em services/
6. Criar endpoint em api/api_v1/endpoints/
7. Registrar rota em api/api_v1/api.py
8. Criar testes em tests/services/ e tests/api/
```

Exemplo de estrutura para um módulo `service_orders`:

```text
models/service_order_model.py
schemas/service_order_schema.py
crud/crud_service_orders.py
services/service_order_service.py
api/api_v1/endpoints/service_orders.py
tests/services/test_service_order_service.py
tests/api/api_v1/endpoints/test_service_orders_endpoint.py
```

A regra principal é: se tiver regra de negócio, coloque no `service`, não no endpoint e não no CRUD.

---

## 12. CRUD abstrato e filtros dinâmicos

O template mantém a proposta de uso de um CRUD abstrato reutilizável para operações comuns, como:

- `get`;
- `get_multi`;
- `get_multi_filter`;
- `get_multi_filters`;
- `get_multi_dynamic_filters`;
- `get_first_by_filters`;
- `get_last_by_filters`;
- `get_aggregates`;
- `create`;
- `create_multi`;
- `update`;
- `update_multi`;
- `remove`.

Exemplo resumido de filtro:

```python
orders = await crud_service_order.get_multi_filters(
    db,
    filters=[
        {"field": "status", "operator": "==", "value": "PENDENTE"},
        {"field": "order_number", "operator": "ilike", "value": "030"},
    ],
    order_by="id",
    order_desc=True,
    limit=100,
)
```

A documentação completa da camada CRUD fica em [`crud/README.md`](crud/README.md).

---

## 13. Regras principais do projeto

### Endpoints

- Não colocar regra de negócio pesada no endpoint.
- Não chamar API externa diretamente no endpoint.
- Não montar queries complexas diretamente na rota.
- Endpoint deve receber, validar, chamar service e retornar.

Leia mais em [`api/api_v1/endpoints/README.md`](api/api_v1/endpoints/README.md).

### Services

- Centralizar regras de negócio.
- Validar duplicidade, status e transições.
- Normalizar dados antes de salvar.
- Orquestrar múltiplos CRUDs quando necessário.
- Chamar clients externos do `core` quando necessário.

Leia mais em [`services/README.md`](services/README.md).

### CRUD

- CRUD deve acessar banco, não decidir regra de negócio.
- Métodos específicos de consulta podem ficar no CRUD específico.
- Evite `HTTPException` no CRUD; prefira levantar erros no service.

Leia mais em [`crud/README.md`](crud/README.md).

### Models

- Model representa tabela.
- Não colocar regra de negócio no model.
- Definir índices em campos usados para busca.
- Importar novos models em `db/base.py`.

Leia mais em [`models/README.md`](models/README.md) e [`db/README.md`](db/README.md).

### Schemas

- Separar schemas de criação, atualização e resposta.
- Usar `ConfigDict(from_attributes=True)` no Pydantic v2.
- Não colocar regra de negócio complexa no schema.

Leia mais em [`schemas/README.md`](schemas/README.md).

### Core

- Centralizar configurações, clients externos e helpers técnicos.
- Não espalhar `httpx.AsyncClient` pelo projeto.
- Não repetir lógica de autenticação externa em vários arquivos.

Leia mais em [`core/README.md`](core/README.md).

### Testes

- Testes de service devem focar regra de negócio.
- Testes de endpoint devem focar contrato HTTP.
- Use mocks para evitar dependência de banco real em testes unitários.

Leia mais em [`tests/README.md`](tests/README.md).

---

## 14. Padrão recomendado para endpoint com service

```python
from typing import Any, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api import deps
from schemas.car_schema import CarCreate, CarUpdate, CarInDbBase
from services.car_service import car_service

router = APIRouter()


@router.get("/", response_model=List[CarInDbBase])
async def read_cars(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    return await car_service.list_cars(
        db=db,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=CarInDbBase)
async def create_car(
    *,
    db: AsyncSession = Depends(deps.get_db),
    car_in: CarCreate,
) -> Any:
    return await car_service.create_car(
        db=db,
        payload=car_in,
    )
```

Esse padrão deixa a rota limpa e preparada para crescimento.

---

## 15. Padrão recomendado para service

```python
from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_cars import car
from schemas.car_schema import CarCreate, CarUpdate


class CarService:
    async def create_car(
        self,
        db: AsyncSession,
        payload: CarCreate,
    ):
        payload.model = payload.model.strip().upper()

        return await car.create(
            db=db,
            obj_in=payload,
        )


car_service = CarService()
```

A versão completa fica em `services/car_service.py`.

---

## 16. Padrão recomendado para API externa

```python
from core.oauth2_client import APIAuthConfig, AuthType, OAuth2APIClient


client = OAuth2APIClient(
    base_url="https://api.parceiro.com.br",
    auth_config=APIAuthConfig(
        auth_type=AuthType.OAUTH2_CLIENT_CREDENTIALS,
        token_url="https://auth.parceiro.com.br/oauth/token",
        client_id="client-id",
        client_secret="client-secret",
        scope="orders.read orders.write",
    ),
)

response = await client.request(
    "POST",
    "/v1/orders",
    data={"order_number": "123"},
)
```

Exemplos específicos ficam em [`examples/oauth2_clients/`](examples/oauth2_clients/).

---

## 17. Comandos úteis

Rodar aplicação:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Rodar testes:

```bash
pytest -v
```

Rodar testes de service:

```bash
pytest tests/services -v
```

Rodar testes de endpoint:

```bash
pytest tests/api -v
```

Instalar dependências principais:

```bash
pip install -r requirements.txt
```

Instalar dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

---

## 18. Convenções gerais

- Use nomes claros e separados por domínio.
- Prefira código assíncrono para novos módulos.
- Use `AsyncSession` como padrão.
- Use `services/` para regra de negócio.
- Use `crud/` para banco.
- Use `core/` para integrações técnicas e recursos globais.
- Use `schemas/` para contratos de entrada e saída.
- Use `tests/` para garantir comportamento antes de evoluir o projeto.
- Mantenha cada pasta documentada com seu próprio `README.md`.

---

## 19. Resumo da arquitetura

```text
Cliente HTTP
    ↓
FastAPI Endpoint
    ↓
Schema Pydantic
    ↓
Service
    ↓
CRUD ou Core Client
    ↓
Banco de dados ou API externa
```

Esse fluxo mantém o projeto organizado, fácil de testar e preparado para crescer sem transformar endpoints em arquivos grandes e difíceis de manter.
