from typing import Any, Dict

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.lastmile_os_sla import (
    atendida_no_prazo_expression,
    latest_travel_subquery,
    sla_expressions,
)
from models.order_types_model import OrderType
from models.service_order_model import ServiceOrder
from models.transport_quotes_model import TransportQuote
from schemas.lastmile_os_overview_schema import LastMileOsOverviewFilters

_EMPTY_ROW = {
    "total": 0,
    "pendente": 0,
    "atendida": 0,
    "atendida_no_prazo": 0,
    "atraso": 0,
    "sem_tecnico": 0,
}


class CRUDLastMileOsOverviewMetrics:
    """Consultas agregadas somente leitura da visão geral LastMile OS."""

    def _type_condition(self, filters: LastMileOsOverviewFilters):
        if filters.type_mode == "in":
            return OrderType.type.in_(filters.type_values)
        return or_(*[OrderType.type.ilike(pattern) for pattern in filters.type_values])

    def _vision_conditions(self, filters: LastMileOsOverviewFilters):
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

    def aggregate_overview_stmt(self, filters: LastMileOsOverviewFilters):
        latest_travel = latest_travel_subquery()
        atraso, _, _ = sla_expressions(
            latest_travel,
            filters.now,
        )
        atendida_no_prazo = atendida_no_prazo_expression(latest_travel)
        return (
            select(
                func.count(ServiceOrder.id).label("total"),
                func.count(ServiceOrder.id)
                .filter(latest_travel.c.end_date.is_(None))
                .label("pendente"),
                func.count(ServiceOrder.id)
                .filter(latest_travel.c.end_date.is_not(None))
                .label("atendida"),
                func.count(ServiceOrder.id)
                .filter(atendida_no_prazo)
                .label("atendida_no_prazo"),
                func.count(ServiceOrder.id).filter(atraso).label("atraso"),
                func.count(ServiceOrder.id)
                .filter(latest_travel.c.driver_id.is_(None))
                .label("sem_tecnico"),
            )
            .select_from(ServiceOrder)
            .join(OrderType, OrderType.id == ServiceOrder.order_type_id)
            .outerjoin(latest_travel, latest_travel.c.order_id == ServiceOrder.id)
            .outerjoin(TransportQuote, TransportQuote.id == latest_travel.c.quote_id)
            .where(and_(*self._vision_conditions(filters)))
        )

    async def aggregate_overview(
        self,
        db: AsyncSession,
        *,
        filters: LastMileOsOverviewFilters,
    ) -> Dict[str, Any]:
        if not filters.type_values:
            return dict(_EMPTY_ROW)

        result = await db.execute(self.aggregate_overview_stmt(filters))
        row = result.mappings().one()
        return dict(row)


crud_lastmile_os_overview_metrics = CRUDLastMileOsOverviewMetrics()
