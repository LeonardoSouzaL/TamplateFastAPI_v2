from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from crud.crud_lastmile_os_metrics import crud_lastmile_os_metrics
from schemas.lastmile_os_status_schema import (
    LastMileOsStatusCountSC,
    LastMileOsStatusFilters,
    LastMileOsStatusResponseSC,
    LastMileOsTypeCountSC,
)

VISION = "LASTMILE"


def parse_csv(value: Optional[str]) -> Optional[List[str]]:
    """None = omitido. Lista vazia = CSV sem itens."""
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_status_csv(value: Optional[str]) -> List[str]:
    items = parse_csv(value)
    if not items:
        return []
    return [item.upper() for item in items]


def resolve_type_filter(
    order_type: Optional[str],
) -> Optional[Tuple[str, List[str]]]:
    """None = CSV vazio (totais 0). Senão (mode, values)."""
    parsed = parse_csv(order_type)
    if parsed is None:
        return "ilike", list(settings.LASTMILE_OS_TYPE_PATTERNS)
    if not parsed:
        return None
    return "in", parsed


def _empty_response(
    *,
    status_filter: List[str],
    finished_filter: Optional[bool],
) -> LastMileOsStatusResponseSC:
    return LastMileOsStatusResponseSC(
        vision=VISION,
        status_filter=status_filter,
        finished_filter=finished_filter,
        total=0,
        universe_total=0,
        by_status=[],
        by_order_type=[],
    )


class LastMileOsStatusService:
    async def get_by_status(
        self,
        *,
        db: AsyncSession,
        status: Optional[str] = None,
        finished: Optional[bool] = None,
        order_type: Optional[str] = None,
        cliente_id: Optional[int] = None,
        designation_id: Optional[int] = None,
        data_inicial: Optional[datetime] = None,
        data_final: Optional[datetime] = None,
    ) -> LastMileOsStatusResponseSC:
        status_filter = parse_status_csv(status)
        type_filter = resolve_type_filter(order_type)
        if type_filter is None:
            return _empty_response(
                status_filter=status_filter,
                finished_filter=finished,
            )

        type_mode, type_values = type_filter
        vision_filters = LastMileOsStatusFilters(
            type_mode=type_mode,
            type_values=type_values,
            cliente_id=cliente_id,
            designation_id=designation_id,
            data_inicial=data_inicial,
            data_final=data_final,
        )
        filtered = LastMileOsStatusFilters(
            type_mode=type_mode,
            type_values=type_values,
            status_types=status_filter,
            finished=finished,
            cliente_id=cliente_id,
            designation_id=designation_id,
            data_inicial=data_inicial,
            data_final=data_final,
        )

        universe_total = await crud_lastmile_os_metrics.count_universe(
            db=db,
            filters=vision_filters,
        )
        rows = await crud_lastmile_os_metrics.aggregate_by_status(
            db=db,
            filters=filtered,
        )

        status_totals: dict[tuple[str, bool], int] = {}
        type_totals: dict[str, int] = {}
        total = 0
        for row in rows:
            quantity = int(row.get("quantity") or 0)
            status_name = str(row.get("status") or "")
            finished_flag = bool(row.get("finished"))
            order_type_name = str(row.get("order_type") or "")
            total += quantity
            status_totals[(status_name, finished_flag)] = (
                status_totals.get((status_name, finished_flag), 0) + quantity
            )
            if order_type_name:
                type_totals[order_type_name] = (
                    type_totals.get(order_type_name, 0) + quantity
                )

        by_status = [
            LastMileOsStatusCountSC(
                status=name,
                finished=flag,
                quantity=qty,
            )
            for (name, flag), qty in status_totals.items()
            if qty
        ]
        by_status.sort(key=lambda item: (-item.quantity, item.status))

        by_order_type = [
            LastMileOsTypeCountSC(order_type=name, quantity=qty)
            for name, qty in type_totals.items()
            if qty
        ]
        by_order_type.sort(key=lambda item: (-item.quantity, item.order_type))

        return LastMileOsStatusResponseSC(
            vision=VISION,
            status_filter=status_filter,
            finished_filter=finished,
            total=total,
            universe_total=universe_total,
            by_status=by_status,
            by_order_type=by_order_type,
        )


lastmile_os_status_service = LastMileOsStatusService()
