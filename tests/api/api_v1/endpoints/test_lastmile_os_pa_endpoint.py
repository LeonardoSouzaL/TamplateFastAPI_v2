from unittest.mock import AsyncMock, patch

import pytest

from schemas.lastmile_os_pa_schema import LastMileOsPaResponseSC


@pytest.mark.asyncio
async def test_os_by_pa_endpoint_deve_retornar_200(async_client):
    expected = LastMileOsPaResponseSC(vision="LASTMILE", total=7, items=[])
    with patch(
        "api.api_v1.endpoints.lastmile_os_pa.lastmile_os_pa_service.get_by_pa",
        new=AsyncMock(return_value=expected),
    ) as mock_service:
        response = await async_client.get(
            "/api/v1/lastmile/orders/by-pa",
            params={
                "cliente_id": 9,
                "designation_id": 24,
                "data_inicial": "2026-09-01T00:00:00Z",
                "data_final": "2026-09-17T23:59:59Z",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 7
    assert body["vision"] == "LASTMILE"
    mock_service.assert_awaited_once()
    kwargs = mock_service.await_args.kwargs
    assert kwargs["cliente_id"] == 9
    assert kwargs["designation_id"] == 24
    assert kwargs["data_inicial"] is not None
    assert kwargs["data_final"] is not None
