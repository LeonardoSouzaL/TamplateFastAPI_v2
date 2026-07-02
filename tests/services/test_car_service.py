import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch

from schemas.car_schema import CarCreate, CarUpdate
from services.car_service import car_service


@pytest.mark.asyncio
async def test_create_car_deve_normalizar_campos_e_chamar_crud():
    """
    Valida a regra do service:
    - normaliza campos antes de salvar;
    - chama o CRUD de criação;
    - retorna o objeto criado.
    """
    db = AsyncMock()
    payload = CarCreate(name=" gol ", plate=" abc1234 ", is_active=True)

    expected = {
        "id": 1,
        "name": "GOL",
        "plate": "ABC1234",
        "is_active": True,
    }

    with patch("services.car_service.car.create", new=AsyncMock(return_value=expected)) as mock_create:
        result = await car_service.create_car(db=db, payload=payload)

    assert result == expected
    assert payload.name == "GOL"
    assert payload.plate == "ABC1234"
    mock_create.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_car_by_id_deve_retornar_carro_quando_existir():
    """
    Valida busca por ID com retorno encontrado.
    """
    db = AsyncMock()
    expected = {"id": 1, "name": "GOL", "plate": "ABC1234", "is_active": True}

    with patch("services.car_service.car.get", new=AsyncMock(return_value=expected)) as mock_get:
        result = await car_service.get_car_by_id(db=db, id=1)

    assert result == expected
    mock_get.assert_awaited_once_with(db=db, id=1)


@pytest.mark.asyncio
async def test_get_car_by_id_deve_retornar_404_quando_nao_existir():
    """
    Valida regra de erro quando o carro não existe.
    """
    db = AsyncMock()

    with patch("services.car_service.car.get", new=AsyncMock(return_value=None)):
        with pytest.raises(HTTPException) as exc:
            await car_service.get_car_by_id(db=db, id=999)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Carro não encontrado."


@pytest.mark.asyncio
async def test_update_car_deve_buscar_registro_e_chamar_update():
    """
    Valida update:
    - busca o registro antes;
    - normaliza campos enviados;
    - chama o CRUD update.
    """
    db = AsyncMock()
    db_car = {"id": 1, "name": "GOL", "plate": "ABC1234", "is_active": True}
    payload = CarUpdate(name=" fox ", plate=" def5678 ")
    expected = {"id": 1, "name": "FOX", "plate": "DEF5678", "is_active": True}

    with patch("services.car_service.car.get", new=AsyncMock(return_value=db_car)), \
         patch("services.car_service.car.update", new=AsyncMock(return_value=expected)) as mock_update:
        result = await car_service.update_car(db=db, id=1, payload=payload)

    assert result == expected
    assert payload.name == "FOX"
    assert payload.plate == "DEF5678"
    mock_update.assert_awaited_once_with(db=db, db_obj=db_car, obj_in=payload)


@pytest.mark.asyncio
async def test_delete_car_deve_buscar_e_remover_registro():
    """
    Valida delete:
    - busca antes para garantir 404 se não existir;
    - remove quando existir.
    """
    db = AsyncMock()
    db_car = {"id": 1, "name": "GOL", "plate": "ABC1234", "is_active": True}

    with patch("services.car_service.car.get", new=AsyncMock(return_value=db_car)), \
         patch("services.car_service.car.remove", new=AsyncMock(return_value=db_car)) as mock_remove:
        result = await car_service.delete_car(db=db, id=1)

    assert result == db_car
    mock_remove.assert_awaited_once_with(db=db, id=1)
