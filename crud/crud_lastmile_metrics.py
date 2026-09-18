from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.travel_route_date import travel_route_date_expression
from models.logistica_groupaditionalinformation_model import AranciaLocation
from models.order_travels_model import OrderTravel
from models.order_types_model import OrderType
from models.service_order_model import ServiceOrder
from models.status_equipament_model import EquipamentStatus
from schemas.lastmile_dashboard_schema import LastMileDashboardFilters


class CRUDLastMileMetrics:
    """Consultas agregadas somente leitura para o dashboard LastMile."""

    def _late_condition(self, now: datetime):
        return and_(
            OrderTravel.end_date.is_not(None),
            OrderTravel.end_date < now,
        )

    def _not_late_condition(self, now: datetime):
        return or_(OrderTravel.end_date.is_(None), OrderTravel.end_date >= now)

    def _start_expr(self):
        return func.coalesce(
            OrderTravel.start_date,
            OrderTravel.route_date,
            OrderTravel.created_at,
        )

    def _apply_shared_filters(self, stmt, filters: LastMileDashboardFilters):
        conditions = [OrderType.type.in_(filters.order_types)]
        effective_date = travel_route_date_expression()

        if filters.data_inicial is not None:
            conditions.append(effective_date >= filters.data_inicial)
        if filters.data_final is not None:
            conditions.append(effective_date <= filters.data_final)
        if filters.designation_id is not None:
            conditions.append(OrderTravel.designation_id == filters.designation_id)
        if filters.sem_motorista:
            conditions.append(OrderTravel.driver_id.is_(None))
        elif filters.driver_id is not None:
            conditions.append(OrderTravel.driver_id == filters.driver_id)
        if filters.carrier_id is not None:
            conditions.append(OrderTravel.carrier_id == filters.carrier_id)
        if filters.cliente_id is not None:
            conditions.append(ServiceOrder.client_id == filters.cliente_id)
        if filters.apenas_nao_finalizada:
            conditions.append(EquipamentStatus.finished.is_(False))
        if filters.apenas_finalizada:
            conditions.append(EquipamentStatus.finished.is_(True))
        if filters.only_late is True:
            conditions.append(self._late_condition(filters.now))
        elif filters.only_late is False:
            conditions.append(self._not_late_condition(filters.now))

        return stmt.where(and_(*conditions))

    async def aggregate_by_pa(
        self,
        db: AsyncSession,
        *,
        filters: LastMileDashboardFilters,
    ) -> List[Dict[str, Any]]:
        if not filters.order_types:
            return []

        start_expr = self._start_expr()
        duration_minutes = func.extract(
            "epoch",
            OrderTravel.end_date - start_expr,
        ) / 60.0

        stmt = select(
            OrderTravel.designation_id.label("pa_id"),
            func.count(OrderTravel.id)
            .filter(EquipamentStatus.finished.is_(False))
            .label("pending"),
            func.count(OrderTravel.id)
            .filter(
                and_(
                    EquipamentStatus.finished.is_(False),
                    OrderTravel.driver_id.is_(None),
                )
            )
            .label("without_driver"),
            func.count(OrderTravel.id)
            .filter(EquipamentStatus.finished.is_(True))
            .label("finished"),
            func.count(OrderTravel.id)
            .filter(self._late_condition(filters.now))
            .label("late"),
            func.avg(duration_minutes)
            .filter(
                and_(
                    EquipamentStatus.finished.is_(True),
                    OrderTravel.end_date.is_not(None),
                )
            )
            .label("avg_minutes"),
        ).select_from(OrderTravel).join(
            ServiceOrder, ServiceOrder.id == OrderTravel.order_id
        ).join(
            OrderType, OrderType.id == ServiceOrder.order_type_id
        ).join(
            EquipamentStatus, EquipamentStatus.id == OrderTravel.status_id
        ).group_by(OrderTravel.designation_id)

        stmt = self._apply_shared_filters(stmt, filters)
        result = await db.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    async def count_metric(
        self,
        db: AsyncSession,
        *,
        filters: LastMileDashboardFilters,
        group_by_client: bool = False,
        group_by_order_type: bool = False,
    ) -> List[Dict[str, Any]]:
        if not filters.order_types:
            return []

        columns: List[Any] = [func.count(OrderTravel.id).label("quantity")]
        group_cols: List[Any] = []
        if group_by_client:
            columns.append(ServiceOrder.client_id.label("client_id"))
            group_cols.append(ServiceOrder.client_id)
        if group_by_order_type:
            columns.append(OrderType.type.label("order_type"))
            group_cols.append(OrderType.type)

        stmt = select(*columns).select_from(OrderTravel).join(
            ServiceOrder, ServiceOrder.id == OrderTravel.order_id
        ).join(
            OrderType, OrderType.id == ServiceOrder.order_type_id
        ).join(
            EquipamentStatus, EquipamentStatus.id == OrderTravel.status_id
        )
        stmt = self._apply_shared_filters(stmt, filters)
        if group_cols:
            stmt = stmt.group_by(*group_cols)

        result = await db.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    async def count_late_by_pa(
        self,
        db: AsyncSession,
        *,
        filters: LastMileDashboardFilters,
    ) -> List[Dict[str, Any]]:
        if not filters.order_types:
            return []

        stmt = select(
            OrderTravel.designation_id.label("pa_id"),
            func.count(OrderTravel.id).label("quantity"),
        ).select_from(OrderTravel).join(
            ServiceOrder, ServiceOrder.id == OrderTravel.order_id
        ).join(
            OrderType, OrderType.id == ServiceOrder.order_type_id
        ).join(
            EquipamentStatus, EquipamentStatus.id == OrderTravel.status_id
        ).group_by(OrderTravel.designation_id)

        stmt = self._apply_shared_filters(stmt, filters)
        result = await db.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    async def get_location_names(
        self,
        db: AsyncSession,
        ids: Sequence[int],
    ) -> Dict[int, Optional[str]]:
        unique_ids = [item for item in set(ids) if item is not None]
        if not unique_ids:
            return {}

        stmt = select(AranciaLocation.id, AranciaLocation.nome).where(
            AranciaLocation.id.in_(unique_ids)
        )
        result = await db.execute(stmt)
        return {row.id: row.nome for row in result.all()}


crud_lastmile_metrics = CRUDLastMileMetrics()
