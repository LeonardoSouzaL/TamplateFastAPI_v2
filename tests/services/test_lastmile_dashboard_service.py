from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from schemas.lastmile_dashboard_schema import LastMileDashboardFilters, TravelMetricType
from services.lastmile_dashboard_service import (
    LastMileDashboardService,
    format_minutes,
    parse_order_types,
)


def _filters(**kwargs) -> LastMileDashboardFilters:
    payload = {
        "order_types": ["LASTMILE"],
        "now": datetime(2026, 9, 16, 12, tzinfo=timezone.utc),
    }
    payload.update(kwargs)
    return LastMileDashboardFilters(**payload)


@pytest.mark.asyncio
async def test_pa_summary_agrupa_pendentes_e_sem_motorista():
    service = LastMileDashboardService()
    db = AsyncMock()
    rows = [
        {
            "pa_id": 10,
            "pending": 2,
            "without_driver": 1,
            "finished": 0,
            "late": 0,
            "avg_minutes": None,
        },
        {
            "pa_id": 20,
            "pending": 0,
            "without_driver": 0,
            "finished": 1,
            "late": 0,
            "avg_minutes": 45,
        },
    ]

    with patch(
        "services.lastmile_dashboard_service.crud_lastmile_metrics.aggregate_by_pa",
        new=AsyncMock(return_value=rows),
    ), patch(
        "services.lastmile_dashboard_service.crud_lastmile_metrics.get_location_names",
        new=AsyncMock(return_value={10: "PA A", 20: "PA B"}),
    ):
        summary = await service.get_pa_summary(db=db)

    assert summary.total_pending == 2
    assert summary.total_without_driver == 1
    assert summary.total_finished == 1
    assert summary.pending_by_pa[0].pa_id == 10
    assert summary.pending_by_pa[0].quantity == 2
    assert summary.average_service_time_by_pa[0].average_minutes == 45
    assert summary.average_service_time_by_pa[0].average_formatted == "00:45"


@pytest.mark.asyncio
async def test_only_without_driver_ignora_driver_id_e_filtra_pendente():
    service = LastMileDashboardService()
    db = AsyncMock()
    captured = {}

    async def fake_agg(*, db, filters):
        captured["filters"] = filters
        return []

    with patch(
        "services.lastmile_dashboard_service.crud_lastmile_metrics.aggregate_by_pa",
        new=fake_agg,
    ):
        await service.get_pa_summary(
            db=db,
            driver_id=99,
            only_without_driver=True,
        )

    filters = captured["filters"]
    assert filters.sem_motorista is True
    assert filters.driver_id is None
    assert filters.apenas_nao_finalizada is True


@pytest.mark.asyncio
async def test_only_pending_vira_where_nao_finalizada():
    service = LastMileDashboardService()
    db = AsyncMock()
    captured = {}

    async def fake_agg(*, db, filters):
        captured["filters"] = filters
        return []

    with patch(
        "services.lastmile_dashboard_service.crud_lastmile_metrics.aggregate_by_pa",
        new=fake_agg,
    ):
        await service.get_pa_summary(db=db, only_pending=True, only_late=False)

    filters = captured["filters"]
    assert filters.apenas_nao_finalizada is True
    assert filters.sem_motorista is False
    assert filters.only_late is False


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        (
            TravelMetricType.pending,
            {
                "apenas_nao_finalizada": True,
                "apenas_finalizada": False,
                "sem_motorista": False,
                "only_late": None,
            },
        ),
        (
            TravelMetricType.without_driver,
            {
                "apenas_nao_finalizada": True,
                "apenas_finalizada": False,
                "sem_motorista": True,
                "only_late": None,
            },
        ),
        (
            TravelMetricType.finished,
            {
                "apenas_nao_finalizada": False,
                "apenas_finalizada": True,
                "sem_motorista": False,
                "only_late": None,
            },
        ),
        (
            TravelMetricType.worst_late_pa,
            {
                "apenas_nao_finalizada": False,
                "apenas_finalizada": False,
                "sem_motorista": False,
                "only_late": True,
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_cada_metric_dispara_pre_filtro_correspondente(metric, expected):
    service = LastMileDashboardService()
    db = AsyncMock()
    captured = {}

    async def fake_count(*, db, filters, group_by_client=False, group_by_order_type=False):
        captured["filters"] = filters
        return []

    async def fake_late(*, db, filters):
        captured["filters"] = filters
        return []

    with patch(
        "services.lastmile_dashboard_service.crud_lastmile_metrics.count_metric",
        new=fake_count,
    ), patch(
        "services.lastmile_dashboard_service.crud_lastmile_metrics.count_late_by_pa",
        new=fake_late,
    ):
        await service.get_metric(db=db, metric=metric, driver_id=7)

    filters = captured["filters"]
    assert filters.apenas_nao_finalizada is expected["apenas_nao_finalizada"]
    assert filters.apenas_finalizada is expected["apenas_finalizada"]
    assert filters.sem_motorista is expected["sem_motorista"]
    assert filters.only_late is expected["only_late"]
    if metric == TravelMetricType.without_driver:
        assert filters.driver_id is None
    else:
        assert filters.driver_id == 7


@pytest.mark.asyncio
async def test_worst_late_pa_retorna_max_por_pa_nao_total():
    service = LastMileDashboardService()
    db = AsyncMock()
    rows = [
        {"pa_id": 1, "quantity": 3},
        {"pa_id": 2, "quantity": 8},
        {"pa_id": 3, "quantity": 5},
    ]

    with patch(
        "services.lastmile_dashboard_service.crud_lastmile_metrics.count_late_by_pa",
        new=AsyncMock(return_value=rows),
    ), patch(
        "services.lastmile_dashboard_service.crud_lastmile_metrics.get_location_names",
        new=AsyncMock(return_value={1: "PA 1", 2: "PA 2", 3: "PA 3"}),
    ):
        result = await service.get_metric(
            db=db,
            metric=TravelMetricType.worst_late_pa,
            group_by_client=True,
        )

    assert result.quantity == 8
    assert result.breakdown[0].pa_id == 2
    assert result.breakdown[0].quantity == 8
    assert result.breakdown[0].client_id is None


@pytest.mark.asyncio
async def test_order_type_omitido_usa_default_lastmile():
    service = LastMileDashboardService()
    db = AsyncMock()
    captured = {}

    async def fake_agg(*, db, filters):
        captured["filters"] = filters
        return []

    with patch(
        "services.lastmile_dashboard_service.crud_lastmile_metrics.aggregate_by_pa",
        new=fake_agg,
    ):
        await service.get_pa_summary(db=db)

    assert captured["filters"].order_types == [
        "LASTMILE",
        "LASTMILE_COLLECT",
        "LASTMILE_DELIVERY",
    ]


@pytest.mark.asyncio
async def test_order_type_csv_vazio_nao_consulta_e_retorna_zero():
    service = LastMileDashboardService()
    db = AsyncMock()
    captured = {}

    async def fake_agg(*, db, filters):
        captured["filters"] = filters
        return []

    with patch(
        "services.lastmile_dashboard_service.crud_lastmile_metrics.aggregate_by_pa",
        new=fake_agg,
    ):
        summary = await service.get_pa_summary(db=db, order_type=" , ")

    assert captured["filters"].order_types == []
    assert summary.total_pending == 0


@pytest.mark.asyncio
async def test_metrics_breakdown_por_cliente_e_tipo():
    service = LastMileDashboardService()
    db = AsyncMock()
    rows = [
        {"quantity": 4, "client_id": 27, "order_type": "LASTMILE"},
        {"quantity": 2, "client_id": 28, "order_type": "LASTMILE_COLLECT"},
    ]

    with patch(
        "services.lastmile_dashboard_service.crud_lastmile_metrics.count_metric",
        new=AsyncMock(return_value=rows),
    ), patch(
        "services.lastmile_dashboard_service.crud_lastmile_metrics.get_location_names",
        new=AsyncMock(return_value={27: "Cliente A", 28: "Cliente B"}),
    ):
        result = await service.get_metric(
            db=db,
            metric=TravelMetricType.pending,
            group_by_client=True,
            group_by_order_type=True,
        )

    assert result.quantity == 6
    assert result.breakdown[0].client_id == 27
    assert result.breakdown[0].client_name == "Cliente A"
    assert result.breakdown[0].order_type == "LASTMILE"
    assert result.breakdown[0].pa_id is None


def test_parse_order_types_respeita_csv_do_front():
    assert parse_order_types("LASTMILE_COLLECT") == ["LASTMILE_COLLECT"]
    assert parse_order_types(None) == [
        "LASTMILE",
        "LASTMILE_COLLECT",
        "LASTMILE_DELIVERY",
    ]
    assert parse_order_types("") == []


def test_format_minutes():
    assert format_minutes(0) == "00:00"
    assert format_minutes(75) == "01:15"


def test_filters_dataclass_defaults():
    filters = _filters(sem_motorista=True, driver_id=None)
    assert filters.sem_motorista is True
    assert filters.apenas_finalizada is False
