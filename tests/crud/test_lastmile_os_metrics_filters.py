from sqlalchemy.dialects import postgresql

from crud.crud_lastmile_os_metrics import CRUDLastMileOsMetrics
from models.order_types_model import OrderType
from models.service_order_model import ServiceOrder
from models.status_equipament_model import EquipamentStatus
from schemas.lastmile_os_status_schema import LastMileOsStatusFilters
from sqlalchemy import func, select


def _compile(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).lower()


def _base_stmt():
    return (
        select(func.count(ServiceOrder.id))
        .select_from(ServiceOrder)
        .join(OrderType, OrderType.id == ServiceOrder.order_type_id)
        .join(EquipamentStatus, EquipamentStatus.id == ServiceOrder.order_state_id)
    )


def test_visao_default_usa_ilike_e_nao_delivery():
    crud = CRUDLastMileOsMetrics()
    filters = LastMileOsStatusFilters(
        type_mode="ilike",
        type_values=[
            "LASTMILE_COLLECT",
            "LASTMILE_NORMAL",
            "LASTMILE_DESINSTAL%",
            "LASTMILE_RETIRADA%",
        ],
    )
    stmt = _base_stmt().where(crud._type_condition(filters))
    compiled = _compile(stmt)
    assert "ilike" in compiled
    assert "lastmile_collect" in compiled
    assert "lastmile_desinstal%" in compiled
    assert "lastmile_delivery" not in compiled


def test_csv_exato_usa_in():
    crud = CRUDLastMileOsMetrics()
    filters = LastMileOsStatusFilters(
        type_mode="in",
        type_values=["LASTMILE_COLLECT", "LASTMILE_NORMAL"],
    )
    stmt = _base_stmt().where(crud._type_condition(filters))
    compiled = _compile(stmt)
    assert " in (" in compiled
    assert "lastmile_collect" in compiled


def test_filtro_status_upper_e_finished():
    crud = CRUDLastMileOsMetrics()
    filters = LastMileOsStatusFilters(
        type_mode="ilike",
        type_values=["LASTMILE_COLLECT"],
        status_types=["PENDING"],
        finished=False,
        designation_id=24,
        cliente_id=10,
    )
    conditions = crud._vision_conditions(filters) + crud._status_conditions(filters)
    stmt = _base_stmt().where(*conditions)
    compiled = _compile(stmt)
    assert "upper" in compiled
    assert "pending" in compiled
    assert "finished" in compiled
    assert "designation_id" in compiled
    assert "client_id" in compiled


def test_visao_filtra_created_at_da_os():
    from datetime import datetime, timezone

    crud = CRUDLastMileOsMetrics()
    inicio = datetime(2026, 9, 1, tzinfo=timezone.utc)
    fim = datetime(2026, 9, 17, tzinfo=timezone.utc)
    filters = LastMileOsStatusFilters(
        type_mode="ilike",
        type_values=["LASTMILE_COLLECT"],
        data_inicial=inicio,
        data_final=fim,
    )
    stmt = _base_stmt().where(*crud._vision_conditions(filters))
    compiled = _compile(stmt)
    assert "created_at" in compiled
    assert "2026-09-01" in compiled
    assert "2026-09-17" in compiled
