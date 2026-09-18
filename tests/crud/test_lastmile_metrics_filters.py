from datetime import datetime, timezone

from sqlalchemy.dialects import postgresql

from crud.crud_lastmile_metrics import CRUDLastMileMetrics
from models.order_travels_model import OrderTravel
from models.order_types_model import OrderType
from models.service_order_model import ServiceOrder
from models.status_equipament_model import EquipamentStatus
from schemas.lastmile_dashboard_schema import LastMileDashboardFilters
from sqlalchemy import func, select


def _compile(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    ).lower()


def test_apply_shared_filters_sem_motorista_ignora_driver_e_usa_is_null():
    crud = CRUDLastMileMetrics()
    now = datetime(2026, 9, 16, tzinfo=timezone.utc)
    filters = LastMileDashboardFilters(
        order_types=["LASTMILE"],
        driver_id=99,
        sem_motorista=True,
        apenas_nao_finalizada=True,
        only_late=True,
        now=now,
    )
    stmt = (
        select(func.count(OrderTravel.id))
        .select_from(OrderTravel)
        .join(ServiceOrder, ServiceOrder.id == OrderTravel.order_id)
        .join(OrderType, OrderType.id == ServiceOrder.order_type_id)
        .join(EquipamentStatus, EquipamentStatus.id == OrderTravel.status_id)
    )
    compiled = _compile(crud._apply_shared_filters(stmt, filters))
    assert "driver_id is null" in compiled
    assert "finished" in compiled
    assert "end_date" in compiled
    assert "order_types.type in" in compiled
    assert "99" not in compiled
