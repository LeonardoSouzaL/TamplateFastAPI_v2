from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.dialects import postgresql

from crud.crud_lastmile_driver_metrics import CRUDLastMileDriverMetrics
from schemas.lastmile_dashboard_schema import LastMileDriverFilters

NOW = datetime(2026, 9, 17, 18, 0, tzinfo=timezone.utc)
DAY = date(2026, 9, 17)


def _compile(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).lower()


def _filters(**kwargs) -> LastMileDriverFilters:
    values = dict(
        order_types=["LASTMILE", "LASTMILE_COLLECT", "LASTMILE_DELIVERY"],
        day=DAY,
        now=NOW,
    )
    values.update(kwargs)
    return LastMileDriverFilters(**values)


def test_visao_default_usa_in_lastmile_e_nao_ilike():
    crud = CRUDLastMileDriverMetrics()
    compiled = _compile(crud.aggregate_status_stmt(_filters()))
    assert "order_types.type in" in compiled
    assert "lastmile_collect" in compiled
    assert "ilike" not in compiled


def test_dia_usa_coalesce_e_fuso_sp():
    crud = CRUDLastMileDriverMetrics()
    compiled = _compile(crud.aggregate_status_stmt(_filters()))
    assert "coalesce" in compiled
    assert "route_date" in compiled
    assert "america/sao_paulo" in compiled
    assert "2026-09-17" in compiled


def test_designation_id_filtra_pa_da_viagem():
    crud = CRUDLastMileDriverMetrics()
    compiled = _compile(
        crud.aggregate_status_stmt(_filters(designation_id=24))
    )
    assert "order_travels.designation_id" in compiled
    assert "24" in compiled


def test_atraso_usa_end_date_e_nao_cotacao():
    crud = CRUDLastMileDriverMetrics()
    compiled = _compile(crud.aggregate_sla_stmt(_filters()))
    assert "end_date" in compiled
    assert "2026-09-17" in compiled
    delayed_part = compiled.split("as delayed")[0]
    assert "estimated_deadline" not in delayed_part


def test_sem_prazo_usa_quote_nula_ou_deadline_zero():
    crud = CRUDLastMileDriverMetrics()
    compiled = _compile(crud.aggregate_sla_stmt(_filters()))
    assert "estimated_deadline" in compiled
    assert "transport_quotes" in compiled


def test_cliente_id_join_service_order():
    crud = CRUDLastMileDriverMetrics()
    compiled = _compile(crud.aggregate_status_stmt(_filters(cliente_id=9)))
    assert "service_order.client_id" in compiled
    assert "9" in compiled


@pytest.mark.asyncio
async def test_csv_vazio_nao_executa_banco():
    crud = CRUDLastMileDriverMetrics()
    db = AsyncMock()
    filters = _filters(order_types=[])
    assert await crud.aggregate_status_by_driver(db=db, filters=filters) == []
    assert await crud.aggregate_sla_by_driver(db=db, filters=filters) == []
    db.execute.assert_not_awaited()
