from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from services.lastmile_dashboard_service import parse_order_types
from services.lastmile_driver_service import LastMileDriverService


def test_default_order_type_e_lastmile_de_viagem():
    types = parse_order_types(None)
    assert types == ["LASTMILE", "LASTMILE_COLLECT", "LASTMILE_DELIVERY"]


@pytest.mark.asyncio
async def test_order_type_csv_vazio_nao_consulta_banco():
    service = LastMileDriverService()
    db = AsyncMock()
    with patch(
        "services.lastmile_driver_service.crud_lastmile_driver_metrics.aggregate_status_by_driver",
        new=AsyncMock(),
    ) as mock_status, patch(
        "services.lastmile_driver_service.crud_lastmile_driver_metrics.aggregate_sla_by_driver",
        new=AsyncMock(),
    ) as mock_sla, patch(
        "services.lastmile_driver_service.crud_lastmile_driver_metrics.get_driver_names",
        new=AsyncMock(),
    ) as mock_names:
        result = await service.get_driver_status_summary(db=db, order_type="")

    mock_status.assert_not_awaited()
    mock_sla.assert_not_awaited()
    mock_names.assert_not_awaited()
    assert result.total_travels == 0
    assert result.total_drivers == 0
    assert result.drivers == []


@pytest.mark.asyncio
async def test_encaminha_filtros_incluindo_pa():
    service = LastMileDriverService()
    captured = {}
    day = date(2026, 9, 17)

    async def fake_status(*, db, filters):
        captured["filters"] = filters
        return []

    with patch(
        "services.lastmile_driver_service.crud_lastmile_driver_metrics.aggregate_status_by_driver",
        new=fake_status,
    ), patch(
        "services.lastmile_driver_service.crud_lastmile_driver_metrics.aggregate_sla_by_driver",
        new=AsyncMock(return_value=[]),
    ), patch(
        "services.lastmile_driver_service.crud_lastmile_driver_metrics.get_driver_names",
        new=AsyncMock(return_value={}),
    ):
        await service.get_driver_status_summary(
            db=AsyncMock(),
            created_at=day,
            designation_id=24,
            driver_id=100,
            carrier_id=3,
            cliente_id=9,
        )

    filters = captured["filters"]
    assert filters.day == day
    assert filters.designation_id == 24
    assert filters.driver_id == 100
    assert filters.carrier_id == 3
    assert filters.cliente_id == 9
    assert "LASTMILE_DELIVERY" in filters.order_types


@pytest.mark.asyncio
async def test_unassigned_e_sla_atraso_v2_sem_cotacao():
    service = LastMileDriverService()
    status_rows = [
        {
            "driver_id": 100,
            "status_id": 1,
            "status_type": "PENDING",
            "status_description": "Pendente",
            "finished": False,
            "quantity": 2,
        },
        {
            "driver_id": None,
            "status_id": 1,
            "status_type": "PENDING",
            "status_description": "Pendente",
            "finished": False,
            "quantity": 3,
        },
        {
            "driver_id": 100,
            "status_id": 2,
            "status_type": "FINISHED",
            "status_description": "Finalizado",
            "finished": True,
            "quantity": 1,
        },
    ]
    sla_rows = [
        {
            "driver_id": 100,
            "total": 3,
            "finished": 1,
            "in_progress": 2,
            "delayed": 1,
            "without_deadline": 0,
        },
        {
            "driver_id": None,
            "total": 3,
            "finished": 0,
            "in_progress": 3,
            "delayed": 0,
            "without_deadline": 3,
        },
    ]

    with patch(
        "services.lastmile_driver_service.crud_lastmile_driver_metrics.aggregate_status_by_driver",
        new=AsyncMock(return_value=status_rows),
    ), patch(
        "services.lastmile_driver_service.crud_lastmile_driver_metrics.aggregate_sla_by_driver",
        new=AsyncMock(return_value=sla_rows),
    ), patch(
        "services.lastmile_driver_service.crud_lastmile_driver_metrics.get_driver_names",
        new=AsyncMock(
            return_value={
                100: {
                    "name": "João",
                    "cod_base": "CTB",
                    "nome_unidade": "Unidade",
                }
            }
        ),
    ) as mock_names:
        result = await service.get_driver_status_summary(
            db=AsyncMock(),
            created_at=date(2026, 9, 17),
        )

    mock_names.assert_awaited_once()
    assert mock_names.await_args.args[1] == [100]
    assert result.total_travels == 6
    assert result.total_drivers == 1
    assert result.unassigned_travels == 3
    assigned = next(item for item in result.drivers if item.driver_uid == 100)
    assert assigned.driver_name == "João"
    assert assigned.cod_base == "CTB"
    assert assigned.total == 3
    assert assigned.sla.delayed == 1
    assert assigned.sla.finished == 1
    assert assigned.sla.in_progress == 2
    unassigned = next(item for item in result.drivers if item.driver_uid is None)
    assert unassigned.total == 3
    assert unassigned.sla.without_deadline == 3
    assert result.date == date(2026, 9, 17)
    assert "estimated_deadline" not in assigned.sla.model_dump()
