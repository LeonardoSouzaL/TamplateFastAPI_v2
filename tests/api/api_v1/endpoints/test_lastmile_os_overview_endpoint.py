from unittest.mock import AsyncMock, patch

import pytest

from schemas.lastmile_os_overview_schema import LastMileOsOverviewResponseSC


@pytest.mark.asyncio
async def test_os_overview_endpoint_deve_retornar_200(async_client):
    expected = LastMileOsOverviewResponseSC(
        vision="LASTMILE",
        total=200,
        pendente_count=50,
        atendida_count=150,
        atendida_no_prazo_count=120,
        fora_do_prazo_count=40,
        sem_tecnico_count=15,
        atendida_no_prazo_percent=60.0,
        fora_do_prazo_percent=20.0,
        efetividade_percent=75.0,
    )
    with patch(
        "api.api_v1.endpoints.lastmile_os_overview.lastmile_os_overview_service.get_overview",
        new=AsyncMock(return_value=expected),
    ) as mock_service:
        response = await async_client.get(
            "/api/v1/lastmile/orders/overview",
            params={
                "cliente_id": 9,
                "designation_id": 24,
                "data_inicial": "2026-09-01T00:00:00Z",
                "data_final": "2026-09-18T23:59:59Z",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["vision"] == "LASTMILE"
    assert body["total"] == 200
    assert body["pendente_count"] == 50
    assert body["atendida_count"] == 150
    assert body["atendida_no_prazo_percent"] == 60.0
    assert body["efetividade_percent"] == 75.0
    mock_service.assert_awaited_once()
    kwargs = mock_service.await_args.kwargs
    assert kwargs["cliente_id"] == 9
    assert kwargs["designation_id"] == 24
    assert kwargs["data_inicial"] is not None
    assert kwargs["data_final"] is not None
