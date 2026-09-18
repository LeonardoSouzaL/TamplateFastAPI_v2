from datetime import datetime
from typing import Any, Dict, List, Sequence

from sqlalchemy import Date, and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from core.travel_route_date import travel_route_date_expression
from models.auth_app_model import AuthApp
from models.order_travels_model import OrderTravel
from models.order_types_model import OrderType
from models.service_order_model import ServiceOrder
from models.status_equipament_model import EquipamentStatus
from models.transport_quotes_model import TransportQuote
from schemas.lastmile_dashboard_schema import LastMileDriverFilters

APP_TZ = "America/Sao_Paulo"


class CRUDLastMileDriverMetrics:
    """Consultas agregadas somente leitura de viagens LastMile por técnico."""

    def _sp_date(self, column) -> ColumnElement:
        return cast(func.timezone(APP_TZ, column), Date)

    def _late_condition(self, now: datetime):
        return and_(
            OrderTravel.end_date.is_not(None),
            OrderTravel.end_date < now,
        )

    def _without_deadline_condition(self):
        return or_(
            TransportQuote.id.is_(None),
            TransportQuote.estimated_deadline.is_(None),
            TransportQuote.estimated_deadline == 0,
        )

    def _apply_shared_filters(self, stmt, filters: LastMileDriverFilters):
        effective_date = travel_route_date_expression()
        conditions = [
            OrderType.type.in_(filters.order_types),
            self._sp_date(effective_date) == filters.day,
        ]
        if filters.designation_id is not None:
            conditions.append(OrderTravel.designation_id == filters.designation_id)
        if filters.driver_id is not None:
            conditions.append(OrderTravel.driver_id == filters.driver_id)
        if filters.carrier_id is not None:
            conditions.append(OrderTravel.carrier_id == filters.carrier_id)
        if filters.cliente_id is not None:
            conditions.append(ServiceOrder.client_id == filters.cliente_id)
        return stmt.where(and_(*conditions))

    def aggregate_status_stmt(self, filters: LastMileDriverFilters):
        stmt = select(
            OrderTravel.driver_id.label("driver_id"),
            EquipamentStatus.id.label("status_id"),
            EquipamentStatus.type.label("status_type"),
            EquipamentStatus.description.label("status_description"),
            EquipamentStatus.finished.label("finished"),
            func.count(OrderTravel.id).label("quantity"),
        ).select_from(OrderTravel).join(
            ServiceOrder, ServiceOrder.id == OrderTravel.order_id
        ).join(
            OrderType, OrderType.id == ServiceOrder.order_type_id
        ).join(
            EquipamentStatus, EquipamentStatus.id == OrderTravel.status_id
        ).group_by(
            OrderTravel.driver_id,
            EquipamentStatus.id,
            EquipamentStatus.type,
            EquipamentStatus.description,
            EquipamentStatus.finished,
        )
        return self._apply_shared_filters(stmt, filters)

    def aggregate_sla_stmt(self, filters: LastMileDriverFilters):
        stmt = select(
            OrderTravel.driver_id.label("driver_id"),
            func.count(OrderTravel.id).label("total"),
            func.count(OrderTravel.id)
            .filter(EquipamentStatus.finished.is_(True))
            .label("finished"),
            func.count(OrderTravel.id)
            .filter(EquipamentStatus.finished.is_(False))
            .label("in_progress"),
            func.count(OrderTravel.id)
            .filter(self._late_condition(filters.now))
            .label("delayed"),
            func.count(OrderTravel.id)
            .filter(self._without_deadline_condition())
            .label("without_deadline"),
        ).select_from(OrderTravel).join(
            ServiceOrder, ServiceOrder.id == OrderTravel.order_id
        ).join(
            OrderType, OrderType.id == ServiceOrder.order_type_id
        ).join(
            EquipamentStatus, EquipamentStatus.id == OrderTravel.status_id
        ).outerjoin(
            TransportQuote, TransportQuote.id == OrderTravel.quote_id
        ).group_by(OrderTravel.driver_id)
        return self._apply_shared_filters(stmt, filters)

    async def aggregate_status_by_driver(
        self,
        db: AsyncSession,
        *,
        filters: LastMileDriverFilters,
    ) -> List[Dict[str, Any]]:
        if not filters.order_types:
            return []

        result = await db.execute(self.aggregate_status_stmt(filters))
        return [dict(row) for row in result.mappings().all()]

    async def aggregate_sla_by_driver(
        self,
        db: AsyncSession,
        *,
        filters: LastMileDriverFilters,
    ) -> List[Dict[str, Any]]:
        if not filters.order_types:
            return []

        result = await db.execute(self.aggregate_sla_stmt(filters))
        return [dict(row) for row in result.mappings().all()]

    async def get_driver_names(
        self,
        db: AsyncSession,
        uids: Sequence[int],
    ) -> Dict[int, Dict[str, Any]]:
        unique_uids = [item for item in set(uids) if item is not None]
        if not unique_uids:
            return {}

        stmt = select(
            AuthApp.uid,
            AuthApp.name,
            AuthApp.cod_base,
            AuthApp.nome_unidade,
        ).where(AuthApp.uid.in_(unique_uids))
        result = await db.execute(stmt)
        return {
            row.uid: {
                "name": row.name,
                "cod_base": row.cod_base,
                "nome_unidade": row.nome_unidade,
            }
            for row in result.all()
        }


crud_lastmile_driver_metrics = CRUDLastMileDriverMetrics()
