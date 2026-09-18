from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from crud.crud_lastmile_metrics import crud_lastmile_metrics
from schemas.lastmile_dashboard_schema import (
    LastMileDashboardFilters,
    PaAverageServiceTimeSC,
    PaCountSC,
    PaLateCountSC,
    PaTravelDashboardSC,
    TravelMetricBreakdownSC,
    TravelMetricResponseSC,
    TravelMetricType,
)


def parse_order_types(order_type: Optional[str]) -> List[str]:
    """None/omitido → tipos LastMile padrão. CSV vazio → lista vazia (totais 0)."""
    if order_type is None:
        return list(settings.LASTMILE_ORDER_TYPES)
    return [item.strip() for item in order_type.split(",") if item.strip()]


def format_minutes(minutes: int) -> str:
    hours, mins = divmod(max(0, minutes), 60)
    return f"{hours:02d}:{mins:02d}"


class LastMileDashboardService:
    def _build_filters(
        self,
        *,
        data_inicial: Optional[datetime] = None,
        data_final: Optional[datetime] = None,
        designation_id: Optional[int] = None,
        driver_id: Optional[int] = None,
        carrier_id: Optional[int] = None,
        cliente_id: Optional[int] = None,
        order_type: Optional[str] = None,
        apenas_nao_finalizada: bool = False,
        apenas_finalizada: bool = False,
        sem_motorista: bool = False,
        only_late: Optional[bool] = None,
        now: Optional[datetime] = None,
    ) -> LastMileDashboardFilters:
        resolved_driver = None if sem_motorista else driver_id
        return LastMileDashboardFilters(
            order_types=parse_order_types(order_type),
            data_inicial=data_inicial,
            data_final=data_final,
            designation_id=designation_id,
            driver_id=resolved_driver,
            carrier_id=carrier_id,
            cliente_id=cliente_id,
            apenas_nao_finalizada=apenas_nao_finalizada,
            apenas_finalizada=apenas_finalizada,
            sem_motorista=sem_motorista,
            only_late=only_late,
            now=now or datetime.now(timezone.utc),
        )

    async def get_pa_summary(
        self,
        *,
        db: AsyncSession,
        data_inicial: Optional[datetime] = None,
        data_final: Optional[datetime] = None,
        designation_id: Optional[int] = None,
        driver_id: Optional[int] = None,
        carrier_id: Optional[int] = None,
        cliente_id: Optional[int] = None,
        order_type: Optional[str] = None,
        only_pending: Optional[bool] = None,
        only_without_driver: Optional[bool] = None,
        only_late: Optional[bool] = None,
    ) -> PaTravelDashboardSC:
        apenas_nao_finalizada = bool(only_pending or only_without_driver)
        filters = self._build_filters(
            data_inicial=data_inicial,
            data_final=data_final,
            designation_id=designation_id,
            driver_id=driver_id if not only_without_driver else None,
            carrier_id=carrier_id,
            cliente_id=cliente_id,
            order_type=order_type,
            apenas_nao_finalizada=apenas_nao_finalizada,
            sem_motorista=bool(only_without_driver),
            only_late=only_late,
        )
        rows = await crud_lastmile_metrics.aggregate_by_pa(db=db, filters=filters)
        if not rows:
            return PaTravelDashboardSC()

        pa_ids = [row.get("pa_id") for row in rows if row.get("pa_id") is not None]
        names = await crud_lastmile_metrics.get_location_names(db, pa_ids)

        pending_items: List[PaCountSC] = []
        without_driver_items: List[PaCountSC] = []
        finished_items: List[PaCountSC] = []
        late_items: List[PaLateCountSC] = []
        avg_items: List[PaAverageServiceTimeSC] = []
        total_pending = 0
        total_without_driver = 0
        total_finished = 0

        for row in rows:
            pa_id = row.get("pa_id")
            pa_name = names.get(pa_id) if pa_id is not None else None
            pending = int(row.get("pending") or 0)
            without_driver = int(row.get("without_driver") or 0)
            finished = int(row.get("finished") or 0)
            late = int(row.get("late") or 0)
            avg_raw = row.get("avg_minutes")

            total_pending += pending
            total_without_driver += without_driver
            total_finished += finished

            if pending:
                pending_items.append(
                    PaCountSC(pa_id=pa_id, pa_name=pa_name, quantity=pending)
                )
            if without_driver:
                without_driver_items.append(
                    PaCountSC(pa_id=pa_id, pa_name=pa_name, quantity=without_driver)
                )
            if finished:
                finished_items.append(
                    PaCountSC(pa_id=pa_id, pa_name=pa_name, quantity=finished)
                )
            if late:
                late_items.append(
                    PaLateCountSC(pa_id=pa_id, pa_name=pa_name, late_count=late)
                )
            if avg_raw is not None:
                avg_minutes = int(avg_raw)
                avg_items.append(
                    PaAverageServiceTimeSC(
                        pa_id=pa_id,
                        pa_name=pa_name,
                        average_minutes=avg_minutes,
                        average_formatted=format_minutes(avg_minutes),
                    )
                )

        pending_items.sort(key=lambda item: (-item.quantity, item.pa_id or 0))
        without_driver_items.sort(key=lambda item: (-item.quantity, item.pa_id or 0))
        finished_items.sort(key=lambda item: (-item.quantity, item.pa_id or 0))
        late_items.sort(key=lambda item: (-item.late_count, item.pa_id or 0))
        avg_items.sort(key=lambda item: (-item.average_minutes, item.pa_id or 0))

        return PaTravelDashboardSC(
            total_pending=total_pending,
            total_without_driver=total_without_driver,
            total_finished=total_finished,
            worst_sla_pa=late_items[0] if late_items else None,
            pending_by_pa=pending_items,
            without_driver_by_pa=without_driver_items,
            finished_by_pa=finished_items,
            average_service_time_by_pa=avg_items,
            late_by_pa=late_items,
        )

    async def get_metric(
        self,
        *,
        db: AsyncSession,
        metric: TravelMetricType,
        data_inicial: Optional[datetime] = None,
        data_final: Optional[datetime] = None,
        designation_id: Optional[int] = None,
        driver_id: Optional[int] = None,
        carrier_id: Optional[int] = None,
        cliente_id: Optional[int] = None,
        order_type: Optional[str] = None,
        group_by_client: bool = False,
        group_by_order_type: bool = False,
    ) -> TravelMetricResponseSC:
        apenas_nao_finalizada = metric in (
            TravelMetricType.pending,
            TravelMetricType.without_driver,
        )
        apenas_finalizada = metric == TravelMetricType.finished
        sem_motorista = metric == TravelMetricType.without_driver
        only_late = True if metric == TravelMetricType.worst_late_pa else None

        filters = self._build_filters(
            data_inicial=data_inicial,
            data_final=data_final,
            designation_id=designation_id,
            driver_id=driver_id,
            carrier_id=carrier_id,
            cliente_id=cliente_id,
            order_type=order_type,
            apenas_nao_finalizada=apenas_nao_finalizada,
            apenas_finalizada=apenas_finalizada,
            sem_motorista=sem_motorista,
            only_late=only_late,
        )

        if metric == TravelMetricType.worst_late_pa:
            return await self._metric_worst_late_pa(
                db=db,
                filters=filters,
                metric=metric,
                group_by_client=group_by_client,
                group_by_order_type=group_by_order_type,
            )

        rows = await crud_lastmile_metrics.count_metric(
            db=db,
            filters=filters,
            group_by_client=group_by_client,
            group_by_order_type=group_by_order_type,
        )
        if not rows:
            return TravelMetricResponseSC(metric=metric, quantity=0, breakdown=[])

        quantity = sum(int(row.get("quantity") or 0) for row in rows)
        breakdown: List[TravelMetricBreakdownSC] = []
        if group_by_client or group_by_order_type:
            client_ids = [
                row.get("client_id")
                for row in rows
                if group_by_client and row.get("client_id") is not None
            ]
            names = await crud_lastmile_metrics.get_location_names(db, client_ids)
            breakdown = [
                TravelMetricBreakdownSC(
                    client_id=row.get("client_id") if group_by_client else None,
                    client_name=(
                        names.get(row.get("client_id"))
                        if group_by_client and row.get("client_id") is not None
                        else None
                    ),
                    order_type=row.get("order_type") if group_by_order_type else None,
                    quantity=int(row.get("quantity") or 0),
                )
                for row in rows
            ]
            breakdown.sort(key=lambda item: (-item.quantity, item.client_id or 0))

        return TravelMetricResponseSC(
            metric=metric,
            quantity=quantity,
            breakdown=breakdown,
        )

    async def _metric_worst_late_pa(
        self,
        *,
        db: AsyncSession,
        filters: LastMileDashboardFilters,
        metric: TravelMetricType,
        group_by_client: bool,
        group_by_order_type: bool,
    ) -> TravelMetricResponseSC:
        rows = await crud_lastmile_metrics.count_late_by_pa(db=db, filters=filters)
        if not rows:
            return TravelMetricResponseSC(metric=metric, quantity=0, breakdown=[])

        pa_ids = [row.get("pa_id") for row in rows if row.get("pa_id") is not None]
        names = await crud_lastmile_metrics.get_location_names(db, pa_ids)

        ranked = sorted(
            rows,
            key=lambda row: (
                -int(row.get("quantity") or 0),
                row.get("pa_id") if row.get("pa_id") is not None else 0,
            ),
        )
        worst = ranked[0]
        quantity = int(worst.get("quantity") or 0)

        breakdown: List[TravelMetricBreakdownSC] = []
        if group_by_client or group_by_order_type:
            breakdown = [
                TravelMetricBreakdownSC(
                    pa_id=row.get("pa_id"),
                    pa_name=names.get(row.get("pa_id")) if row.get("pa_id") is not None else None,
                    quantity=int(row.get("quantity") or 0),
                )
                for row in ranked
            ]

        return TravelMetricResponseSC(
            metric=metric,
            quantity=quantity,
            breakdown=breakdown,
        )


lastmile_dashboard_service = LastMileDashboardService()
