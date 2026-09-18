from typing import Any, Dict, List

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.order_types_model import OrderType
from models.service_order_model import ServiceOrder
from models.status_equipament_model import EquipamentStatus
from schemas.lastmile_os_status_schema import LastMileOsStatusFilters


class CRUDLastMileOsMetrics:
    """Consultas agregadas somente leitura de OS LastMile por status."""

    def _type_condition(self, filters: LastMileOsStatusFilters):
        if filters.type_mode == "in":
            return OrderType.type.in_(filters.type_values)
        return or_(*[OrderType.type.ilike(pattern) for pattern in filters.type_values])

    def _vision_conditions(self, filters: LastMileOsStatusFilters):
        conditions = [self._type_condition(filters)]
        if filters.cliente_id is not None:
            conditions.append(ServiceOrder.client_id == filters.cliente_id)
        if filters.designation_id is not None:
            conditions.append(ServiceOrder.designation_id == filters.designation_id)
        if filters.data_inicial is not None:
            conditions.append(ServiceOrder.created_at >= filters.data_inicial)
        if filters.data_final is not None:
            conditions.append(ServiceOrder.created_at <= filters.data_final)
        return conditions

    def _status_conditions(self, filters: LastMileOsStatusFilters):
        conditions = []
        if filters.status_types:
            conditions.append(func.upper(EquipamentStatus.type).in_(filters.status_types))
        if filters.finished is not None:
            conditions.append(EquipamentStatus.finished.is_(filters.finished))
        return conditions

    async def count_universe(
        self,
        db: AsyncSession,
        *,
        filters: LastMileOsStatusFilters,
    ) -> int:
        if not filters.type_values:
            return 0

        stmt = select(func.count(ServiceOrder.id)).select_from(ServiceOrder).join(
            OrderType, OrderType.id == ServiceOrder.order_type_id
        ).join(
            EquipamentStatus, EquipamentStatus.id == ServiceOrder.order_state_id
        ).where(and_(*self._vision_conditions(filters)))
        result = await db.execute(stmt)
        return int(result.scalar_one() or 0)

    async def aggregate_by_status(
        self,
        db: AsyncSession,
        *,
        filters: LastMileOsStatusFilters,
    ) -> List[Dict[str, Any]]:
        if not filters.type_values:
            return []

        status_key = func.upper(EquipamentStatus.type)
        conditions = self._vision_conditions(filters) + self._status_conditions(filters)
        stmt = select(
            status_key.label("status"),
            EquipamentStatus.finished.label("finished"),
            OrderType.type.label("order_type"),
            func.count(ServiceOrder.id).label("quantity"),
        ).select_from(ServiceOrder).join(
            OrderType, OrderType.id == ServiceOrder.order_type_id
        ).join(
            EquipamentStatus, EquipamentStatus.id == ServiceOrder.order_state_id
        ).where(and_(*conditions)).group_by(
            status_key,
            EquipamentStatus.finished,
            OrderType.type,
        )
        result = await db.execute(stmt)
        return [dict(row) for row in result.mappings().all()]


crud_lastmile_os_metrics = CRUDLastMileOsMetrics()
