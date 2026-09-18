from typing import Any, Dict, List

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.lastmile_os_sla import latest_travel_subquery, sla_expressions
from models.order_types_model import OrderType
from models.service_order_model import ServiceOrder
from models.status_equipament_model import EquipamentStatus
from models.transport_quotes_model import TransportQuote
from schemas.lastmile_os_pa_schema import LastMileOsPaFilters


class CRUDLastMileOsPaMetrics:
    """Consultas agregadas somente leitura de OS LastMile por PA."""

    def _type_condition(self, filters: LastMileOsPaFilters):
        if filters.type_mode == "in":
            return OrderType.type.in_(filters.type_values)
        return or_(*[OrderType.type.ilike(pattern) for pattern in filters.type_values])

    def _vision_conditions(self, filters: LastMileOsPaFilters):
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

    def aggregate_by_pa_stmt(self, filters: LastMileOsPaFilters):
        latest_travel = latest_travel_subquery()
        atraso, dentro_do_prazo, sem_prazo = sla_expressions(
            latest_travel,
            filters.now,
        )
        return (
            select(
                ServiceOrder.designation_id.label("pa_id"),
                func.count(ServiceOrder.id).label("chamado_count"),
                func.count(ServiceOrder.id)
                .filter(latest_travel.c.driver_id.is_(None))
                .label("sem_tecnico"),
                func.count(ServiceOrder.id).filter(atraso).label("atraso"),
                func.count(ServiceOrder.id)
                .filter(dentro_do_prazo)
                .label("dentro_do_prazo"),
                func.count(ServiceOrder.id).filter(sem_prazo).label("sem_prazo"),
            )
            .select_from(ServiceOrder)
            .join(OrderType, OrderType.id == ServiceOrder.order_type_id)
            .outerjoin(latest_travel, latest_travel.c.order_id == ServiceOrder.id)
            .outerjoin(TransportQuote, TransportQuote.id == latest_travel.c.quote_id)
            .where(and_(*self._vision_conditions(filters)))
            .group_by(ServiceOrder.designation_id)
        )

    def aggregate_travel_status_stmt(self, filters: LastMileOsPaFilters):
        latest_travel = latest_travel_subquery()
        status_key = func.upper(EquipamentStatus.type)
        return (
            select(
                ServiceOrder.designation_id.label("pa_id"),
                status_key.label("status"),
                func.count(ServiceOrder.id).label("quantity"),
            )
            .select_from(ServiceOrder)
            .join(OrderType, OrderType.id == ServiceOrder.order_type_id)
            .join(latest_travel, latest_travel.c.order_id == ServiceOrder.id)
            .join(EquipamentStatus, EquipamentStatus.id == latest_travel.c.status_id)
            .where(and_(*self._vision_conditions(filters)))
            .group_by(ServiceOrder.designation_id, status_key)
        )

    async def aggregate_by_pa(
        self,
        db: AsyncSession,
        *,
        filters: LastMileOsPaFilters,
    ) -> List[Dict[str, Any]]:
        if not filters.type_values:
            return []

        result = await db.execute(self.aggregate_by_pa_stmt(filters))
        return [dict(row) for row in result.mappings().all()]

    async def aggregate_travel_status_by_pa(
        self,
        db: AsyncSession,
        *,
        filters: LastMileOsPaFilters,
    ) -> List[Dict[str, Any]]:
        if not filters.type_values:
            return []

        result = await db.execute(self.aggregate_travel_status_stmt(filters))
        return [dict(row) for row in result.mappings().all()]


crud_lastmile_os_pa_metrics = CRUDLastMileOsPaMetrics()
