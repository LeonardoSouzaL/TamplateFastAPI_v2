from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from schemas.lastmile_dashboard_schema import (
    DriverTravelStatusSummarySC,
    TravelMetricResponseSC,
    TravelMetricType,
)


@pytest.mark.asyncio
async def test_pa_summary_endpoint_deve_retornar_200(async_client):
    expected = {
        "total_pending": 2,
        "total_without_driver": 1,
        "total_finished": 1,
        "worst_sla_pa": None,
        "pending_by_pa": [],
        "without_driver_by_pa": [],
        "finished_by_pa": [],
        "average_service_time_by_pa": [],
        "late_by_pa": [],
    }
    with patch(
        "api.api_v1.endpoints.lastmile_dashboard.lastmile_dashboard_service.get_pa_summary",
        new=AsyncMock(return_value=expected),
    ) as mock_service:
        response = await async_client.get("/api/v1/lastmile/dashboard/pa-summary")

    assert response.status_code == 200
    assert response.json()["total_pending"] == 2
    mock_service.assert_awaited_once()


@pytest.mark.asyncio
async def test_metrics_endpoint_todos_os_tipos(async_client):
    with patch(
        "api.api_v1.endpoints.lastmile_dashboard.lastmile_dashboard_service.get_metric",
        new=AsyncMock(
            return_value=TravelMetricResponseSC(
                metric=TravelMetricType.pending,
                quantity=3,
            )
        ),
    ) as mock_service:
        for metric in TravelMetricType:
            response = await async_client.get(
                "/api/v1/lastmile/dashboard/metrics",
                params={"metric": metric.value},
            )
            assert response.status_code == 200
            assert response.json()["quantity"] == 3
    assert mock_service.await_count == len(TravelMetricType)


@pytest.mark.asyncio
async def test_driver_status_summary_endpoint_deve_retornar_200(async_client):
    expected = DriverTravelStatusSummarySC(
        date=date(2026, 9, 17),
        total_travels=6,
        total_drivers=1,
        unassigned_travels=3,
        by_status_global=[],
        drivers=[],
    )
    with patch(
        "api.api_v1.endpoints.lastmile_dashboard.lastmile_driver_service.get_driver_status_summary",
        new=AsyncMock(return_value=expected),
    ) as mock_service:
        response = await async_client.get(
            "/api/v1/lastmile/dashboard/driver-status-summary",
            params={
                "created_at": "2026-09-17",
                "designation_id": 24,
                "driver_id": 100,
                "carrier_id": 3,
                "cliente_id": 9,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total_travels"] == 6
    assert body["total_drivers"] == 1
    assert body["unassigned_travels"] == 3
    mock_service.assert_awaited_once()
    kwargs = mock_service.await_args.kwargs
    assert kwargs["created_at"] == date(2026, 9, 17)
    assert kwargs["designation_id"] == 24
    assert kwargs["driver_id"] == 100
    assert kwargs["carrier_id"] == 3
    assert kwargs["cliente_id"] == 9
