from unittest.mock import AsyncMock, patch

import pytest

from schemas.lastmile_os_status_schema import LastMileOsStatusResponseSC


@pytest.mark.asyncio
async def test_os_by_status_endpoint_deve_retornar_200(async_client):
    expected = LastMileOsStatusResponseSC(
        vision="LASTMILE",
        status_filter=["PENDING"],
        finished_filter=None,
        total=20,
        universe_total=100,
        by_status=[],
        by_order_type=[],
    )
    with patch(
        "api.api_v1.endpoints.lastmile_os_status.lastmile_os_status_service.get_by_status",
        new=AsyncMock(return_value=expected),
    ) as mock_service:
        response = await async_client.get(
            "/api/v1/lastmile/orders/by-status",
            params={
                "status": "PENDING",
                "data_inicial": "2026-09-01T00:00:00Z",
                "data_final": "2026-09-17T23:59:59Z",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 20
    assert body["universe_total"] == 100
    assert body["status_filter"] == ["PENDING"]
    mock_service.assert_awaited_once()
    kwargs = mock_service.await_args.kwargs
    assert kwargs["status"] == "PENDING"
    assert kwargs["data_inicial"] is not None
    assert kwargs["data_final"] is not None
