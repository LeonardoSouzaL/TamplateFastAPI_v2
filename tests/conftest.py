import pytest
from httpx import AsyncClient

from main import app


@pytest.fixture
async def async_client():
    """
    Cliente HTTP assíncrono para testar endpoints FastAPI.

    Observação:
    - Esse fixture usa a aplicação real importada de main.py.
    - Para testes com banco real de teste, sobrescreva a dependência deps.get_db.
    - Para testes isolados de endpoint, use monkeypatch para mockar o service.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def car_payload():
    """
    Payload padrão para criação de carro.
    """
    return {
        "name": "Gol",
        "plate": "abc1234",
        "is_active": True,
    }


@pytest.fixture
def car_response():
    """
    Resposta padrão simulando um carro vindo do banco.
    """
    return {
        "id": 1,
        "name": "GOL",
        "plate": "ABC1234",
        "is_active": True,
    }
