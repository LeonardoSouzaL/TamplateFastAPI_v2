from typing import Any, Dict, List, Sequence, Set

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.lastmile_os_sla import latest_travel_subquery, sla_expressions, sp_date
from models.auth_app_model import AuthApp
from models.order_travels_model import OrderTravel
from models.order_types_model import OrderType
from models.service_order_model import ServiceOrder
from models.status_equipament_model import EquipamentStatus
from models.transport_quotes_model import TransportQuote
from schemas.lastmile_os_driver_schema import LastMileOsDriverFilters


class CRUDLastMileOsDriverMetrics:
    """Consultas agregadas somente leitura de OS LastMile por técnico."""

    def _type_condition(self, filters: LastMileOsDriverFilters):
        if filters.type_mode == "in":
            return OrderType.type.in_(filters.type_values)
        return or_(*[OrderType.type.ilike(pattern) for pattern in filters.type_values])

    def _vision_conditions(self, filters: LastMileOsDriverFilters):
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

    def _apply_driver_filter(
        self,
        stmt,
        filters: LastMileOsDriverFilters,
        latest_travel,
    ):
        if filters.driver_id is not None:
            return stmt.where(latest_travel.c.driver_id == filters.driver_id)
        return stmt

    def aggregate_by_driver_stmt(self, filters: LastMileOsDriverFilters):
        latest_travel = latest_travel_subquery()
        atraso, dentro_do_prazo, sem_prazo = sla_expressions(
            latest_travel,
            filters.now,
        )
        stmt = (
            select(
                latest_travel.c.driver_id.label("driver_id"),
                func.count(ServiceOrder.id).label("chamado_count"),
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
        )
        stmt = self._apply_driver_filter(stmt, filters, latest_travel)
        return stmt.group_by(latest_travel.c.driver_id)

    def aggregate_travel_status_stmt(self, filters: LastMileOsDriverFilters):
        latest_travel = latest_travel_subquery()
        status_key = func.upper(EquipamentStatus.type)
        stmt = (
            select(
                latest_travel.c.driver_id.label("driver_id"),
                status_key.label("status"),
                func.count(ServiceOrder.id).label("quantity"),
            )
            .select_from(ServiceOrder)
            .join(OrderType, OrderType.id == ServiceOrder.order_type_id)
            .join(latest_travel, latest_travel.c.order_id == ServiceOrder.id)
            .join(EquipamentStatus, EquipamentStatus.id == latest_travel.c.status_id)
            .where(
                and_(
                    *self._vision_conditions(filters),
                    latest_travel.c.driver_id.is_not(None),
                )
            )
        )
        stmt = self._apply_driver_filter(stmt, filters, latest_travel)
        return stmt.group_by(latest_travel.c.driver_id, status_key)

    def list_drivers_with_route_today_stmt(
        self,
        filters: LastMileOsDriverFilters,
        uids: Sequence[int],
    ):
        today = sp_date(filters.now)
        return (
            select(OrderTravel.driver_id)
            .distinct()
            .select_from(OrderTravel)
            .join(ServiceOrder, ServiceOrder.id == OrderTravel.order_id)
            .join(OrderType, OrderType.id == ServiceOrder.order_type_id)
            .where(
                and_(
                    self._type_condition(filters),
                    OrderTravel.driver_id.in_(list(uids)),
                    OrderTravel.route_date.is_not(None),
                    sp_date(OrderTravel.route_date) == today,
                )
            )
        )

    async def aggregate_by_driver(
        self,
        db: AsyncSession,
        *,
        filters: LastMileOsDriverFilters,
    ) -> List[Dict[str, Any]]:
        if not filters.type_values:
            return []

        result = await db.execute(self.aggregate_by_driver_stmt(filters))
        return [dict(row) for row in result.mappings().all()]

    async def aggregate_travel_status_by_driver(
        self,
        db: AsyncSession,
        *,
        filters: LastMileOsDriverFilters,
    ) -> List[Dict[str, Any]]:
        if not filters.type_values:
            return []

        result = await db.execute(self.aggregate_travel_status_stmt(filters))
        return [dict(row) for row in result.mappings().all()]

    async def list_drivers_with_route_today(
        self,
        db: AsyncSession,
        *,
        filters: LastMileOsDriverFilters,
        uids: Sequence[int],
    ) -> Set[int]:
        unique_uids = [item for item in set(uids) if item is not None]
        if not unique_uids or not filters.type_values:
            return set()

        result = await db.execute(
            self.list_drivers_with_route_today_stmt(filters, unique_uids)
        )
        return {row[0] for row in result.all() if row[0] is not None}

    def get_driver_profiles_stmt(self, uids: Sequence[int]):
        return select(
            AuthApp.uid,
            AuthApp.name,
            AuthApp.cod_base,
            AuthApp.nome_unidade,
            AuthApp.last_opening,
        ).where(AuthApp.uid.in_(list(uids)))

    async def get_driver_profiles(
        self,
        db: AsyncSession,
        uids: Sequence[int],
    ) -> Dict[int, Dict[str, Any]]:
        unique_uids = [item for item in set(uids) if item is not None]
        if not unique_uids:
            return {}

        result = await db.execute(self.get_driver_profiles_stmt(unique_uids))
        return {
            row.uid: {
                "name": row.name,
                "cod_base": row.cod_base,
                "nome_unidade": row.nome_unidade,
                "last_opening": row.last_opening,
            }
            for row in result.all()
        }


crud_lastmile_os_driver_metrics = CRUDLastMileOsDriverMetrics()
