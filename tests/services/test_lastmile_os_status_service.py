from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from services.lastmile_os_status_service import (
    LastMileOsStatusService,
    parse_status_csv,
    resolve_type_filter,
)


def test_parse_status_csv_normaliza_para_upper():
    assert parse_status_csv("Pending, ON ROUTE") == ["PENDING", "ON ROUTE"]
    assert parse_status_csv(None) == []
    assert parse_status_csv("  ") == []


def test_resolve_type_filter_default_nao_usa_delivery():
    mode, values = resolve_type_filter(None)
    assert mode == "ilike"
    assert "LASTMILE_DELIVERY" not in values
    assert "LASTMILE_COLLECT" in values
    assert "LASTMILE_NORMAL" in values
    assert any(item.startswith("LASTMILE_DESINSTAL") for item in values)
    assert any(item.startswith("LASTMILE_RETIRADA") for item in values)


def test_resolve_type_filter_csv_vazio_retorna_none():
    assert resolve_type_filter("") is None
    assert resolve_type_filter(" , ") is None


def test_resolve_type_filter_csv_exato():
    mode, values = resolve_type_filter("LASTMILE_COLLECT, LASTMILE_NORMAL")
    assert mode == "in"
    assert values == ["LASTMILE_COLLECT", "LASTMILE_NORMAL"]


@pytest.mark.asyncio
async def test_sem_filtro_total_igual_universe():
    service = LastMileOsStatusService()
    db = AsyncMock()
    rows = [
        {
            "status": "PENDING",
            "finished": False,
            "order_type": "LASTMILE_COLLECT",
            "quantity": 10,
        },
        {
            "status": "SUCCESS",
            "finished": True,
            "order_type": "LASTMILE_NORMAL",
            "quantity": 5,
        },
    ]
    with patch(
        "services.lastmile_os_status_service.crud_lastmile_os_metrics.count_universe",
        new=AsyncMock(return_value=15),
    ), patch(
        "services.lastmile_os_status_service.crud_lastmile_os_metrics.aggregate_by_status",
        new=AsyncMock(return_value=rows),
    ):
        result = await service.get_by_status(db=db)

    assert result.total == 15
    assert result.universe_total == 15
    assert result.finished_filter is None
    assert result.status_filter == []


@pytest.mark.asyncio
async def test_status_pending_nao_inclui_on_route_nem_new():
    service = LastMileOsStatusService()
    db = AsyncMock()
    captured = {}

    async def fake_agg(*, db, filters):
        captured["filters"] = filters
        return [
            {
                "status": "PENDING",
                "finished": False,
                "order_type": "LASTMILE_DESINSTALAÇÃO",
                "quantity": 20,
            }
        ]

    with patch(
        "services.lastmile_os_status_service.crud_lastmile_os_metrics.count_universe",
        new=AsyncMock(return_value=100),
    ), patch(
        "services.lastmile_os_status_service.crud_lastmile_os_metrics.aggregate_by_status",
        new=fake_agg,
    ):
        result = await service.get_by_status(db=db, status="Pending")

    assert captured["filters"].status_types == ["PENDING"]
    assert result.total == 20
    assert result.universe_total == 100
    assert result.status_filter == ["PENDING"]
    assert [item.status for item in result.by_status] == ["PENDING"]


@pytest.mark.asyncio
async def test_finished_false_soma_abertos():
    service = LastMileOsStatusService()
    db = AsyncMock()
    captured = {}

    async def fake_agg(*, db, filters):
        captured["filters"] = filters
        return [
            {
                "status": "PENDING",
                "finished": False,
                "order_type": "LASTMILE_COLLECT",
                "quantity": 8,
            },
            {
                "status": "ON ROUTE",
                "finished": False,
                "order_type": "LASTMILE_DESINSTALAÇÃO",
                "quantity": 2,
            },
        ]

    with patch(
        "services.lastmile_os_status_service.crud_lastmile_os_metrics.count_universe",
        new=AsyncMock(return_value=50),
    ), patch(
        "services.lastmile_os_status_service.crud_lastmile_os_metrics.aggregate_by_status",
        new=fake_agg,
    ):
        result = await service.get_by_status(db=db, finished=False)

    assert captured["filters"].finished is False
    assert result.total == 10
    assert result.finished_filter is False
    assert {item.status for item in result.by_status} == {"PENDING", "ON ROUTE"}


@pytest.mark.asyncio
async def test_pending_and_finished_true_zera_recorte():
    service = LastMileOsStatusService()
    db = AsyncMock()
    captured = {}

    async def fake_agg(*, db, filters):
        captured["filters"] = filters
        return []

    with patch(
        "services.lastmile_os_status_service.crud_lastmile_os_metrics.count_universe",
        new=AsyncMock(return_value=40),
    ), patch(
        "services.lastmile_os_status_service.crud_lastmile_os_metrics.aggregate_by_status",
        new=fake_agg,
    ):
        result = await service.get_by_status(db=db, status="PENDING", finished=True)

    assert captured["filters"].status_types == ["PENDING"]
    assert captured["filters"].finished is True
    assert result.total == 0
    assert result.universe_total == 40
    assert result.by_status == []
    assert result.by_order_type == []


@pytest.mark.asyncio
async def test_order_type_csv_vazio_nao_consulta_banco():
    service = LastMileOsStatusService()
    db = AsyncMock()
    with patch(
        "services.lastmile_os_status_service.crud_lastmile_os_metrics.count_universe",
        new=AsyncMock(),
    ) as mock_universe, patch(
        "services.lastmile_os_status_service.crud_lastmile_os_metrics.aggregate_by_status",
        new=AsyncMock(),
    ) as mock_agg:
        result = await service.get_by_status(db=db, order_type="")

    mock_universe.assert_not_awaited()
    mock_agg.assert_not_awaited()
    assert result.total == 0
    assert result.universe_total == 0


@pytest.mark.asyncio
async def test_encaminha_data_inicial_e_final_para_visao_e_recorte():
    service = LastMileOsStatusService()
    db = AsyncMock()
    captured = {}
    inicio = datetime(2026, 9, 1, tzinfo=timezone.utc)
    fim = datetime(2026, 9, 17, tzinfo=timezone.utc)

    async def fake_universe(*, db, filters):
        captured["universe"] = filters
        return 12

    async def fake_agg(*, db, filters):
        captured["filtered"] = filters
        return []

    with patch(
        "services.lastmile_os_status_service.crud_lastmile_os_metrics.count_universe",
        new=fake_universe,
    ), patch(
        "services.lastmile_os_status_service.crud_lastmile_os_metrics.aggregate_by_status",
        new=fake_agg,
    ):
        await service.get_by_status(
            db=db,
            status="PENDING",
            data_inicial=inicio,
            data_final=fim,
        )

    assert captured["universe"].data_inicial == inicio
    assert captured["universe"].data_final == fim
    assert captured["filtered"].data_inicial == inicio
    assert captured["filtered"].data_final == fim
    assert captured["filtered"].status_types == ["PENDING"]
