import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_list_cars_endpoint_deve_retornar_200(async_client, car_response):
    """
    Testa o endpoint GET /api/v1/cars/ mockando o service.
    """
    with patch(
        "api.api_v1.endpoints.cars.car_service.list_cars",
        new=AsyncMock(return_value=[car_response]),
    ) as mock_service:
        response = await async_client.get("/api/v1/cars/")

    assert response.status_code == 200
    assert response.json() == [car_response]
    mock_service.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_car_endpoint_deve_retornar_200(async_client, car_response):
    """
    Testa o endpoint GET /api/v1/cars/{id} mockando o service.
    """
    with patch(
        "api.api_v1.endpoints.cars.car_service.get_car_by_id",
        new=AsyncMock(return_value=car_response),
    ) as mock_service:
        response = await async_client.get("/api/v1/cars/1")

    assert response.status_code == 200
    assert response.json() == car_response
    mock_service.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_car_endpoint_deve_retornar_200(async_client, car_payload, car_response):
    """
    Testa o endpoint POST /api/v1/cars/ mockando o service.
    """
    with patch(
        "api.api_v1.endpoints.cars.car_service.create_car",
        new=AsyncMock(return_value=car_response),
    ) as mock_service:
        response = await async_client.post("/api/v1/cars/", json=car_payload)

    assert response.status_code == 200
    assert response.json() == car_response
    mock_service.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_car_endpoint_deve_retornar_200(async_client, car_response):
    """
    Testa o endpoint PUT /api/v1/cars/{id} mockando o service.
    """
    payload = {"name": "Fox", "plate": "DEF5678", "is_active": True}
    expected = {**car_response, **{"name": "FOX", "plate": "DEF5678"}}

    with patch(
        "api.api_v1.endpoints.cars.car_service.update_car",
        new=AsyncMock(return_value=expected),
    ) as mock_service:
        response = await async_client.put("/api/v1/cars/1", json=payload)

    assert response.status_code == 200
    assert response.json() == expected
    mock_service.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_car_endpoint_deve_retornar_200(async_client, car_response):
    """
    Testa o endpoint DELETE /api/v1/cars/{id} mockando o service.
    """
    with patch(
        "api.api_v1.endpoints.cars.car_service.delete_car",
        new=AsyncMock(return_value=car_response),
    ) as mock_service:
        response = await async_client.delete("/api/v1/cars/1")

    assert response.status_code == 200
    assert response.json() == car_response
    mock_service.assert_awaited_once()
