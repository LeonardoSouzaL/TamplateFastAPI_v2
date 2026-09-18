from datetime import date, datetime, timedelta, timezone, tzinfo
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_lastmile_driver_metrics import crud_lastmile_driver_metrics
from schemas.lastmile_dashboard_schema import (
    DriverTravelSlaSC,
    DriverTravelStatusSummaryItemSC,
    DriverTravelStatusSummarySC,
    LastMileDriverFilters,
    TravelStatusCountSC,
)
from services.lastmile_dashboard_service import parse_order_types


def _app_tz() -> tzinfo:
    try:
        return ZoneInfo("America/Sao_Paulo")
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=-3))


def _empty_response(day: date) -> DriverTravelStatusSummarySC:
    return DriverTravelStatusSummarySC(
        date=day,
        total_travels=0,
        total_drivers=0,
        unassigned_travels=0,
        by_status_global=[],
        drivers=[],
    )


def _resolve_day(created_at: Optional[date]) -> date:
    if created_at is not None:
        return created_at
    return datetime.now(_app_tz()).date()


def _status_sort_key(item: TravelStatusCountSC):
    return (-item.count, item.status_type)


class LastMileDriverService:
    def _build_filters(
        self,
        *,
        created_at: Optional[date] = None,
        designation_id: Optional[int] = None,
        driver_id: Optional[int] = None,
        carrier_id: Optional[int] = None,
        cliente_id: Optional[int] = None,
        order_type: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> LastMileDriverFilters:
        return LastMileDriverFilters(
            order_types=parse_order_types(order_type),
            day=_resolve_day(created_at),
            designation_id=designation_id,
            driver_id=driver_id,
            carrier_id=carrier_id,
            cliente_id=cliente_id,
            now=now or datetime.now(timezone.utc),
        )

    def _to_status_list(
        self,
        rows: List[dict],
    ) -> List[TravelStatusCountSC]:
        items = [
            TravelStatusCountSC(
                status_id=int(row.get("status_id") or 0),
                status_type=row.get("status_type") or "SEM_STATUS",
                status_description=row.get("status_description"),
                finished=bool(row.get("finished")),
                count=int(row.get("quantity") or 0),
            )
            for row in rows
        ]
        items.sort(key=_status_sort_key)
        return items

    async def get_driver_status_summary(
        self,
        *,
        db: AsyncSession,
        created_at: Optional[date] = None,
        designation_id: Optional[int] = None,
        driver_id: Optional[int] = None,
        carrier_id: Optional[int] = None,
        cliente_id: Optional[int] = None,
        order_type: Optional[str] = None,
    ) -> DriverTravelStatusSummarySC:
        filters = self._build_filters(
            created_at=created_at,
            designation_id=designation_id,
            driver_id=driver_id,
            carrier_id=carrier_id,
            cliente_id=cliente_id,
            order_type=order_type,
        )
        if not filters.order_types:
            return _empty_response(filters.day)

        status_rows = await crud_lastmile_driver_metrics.aggregate_status_by_driver(
            db=db,
            filters=filters,
        )
        if not status_rows:
            return _empty_response(filters.day)

        sla_rows = await crud_lastmile_driver_metrics.aggregate_sla_by_driver(
            db=db,
            filters=filters,
        )
        sla_by_uid: Dict[Optional[int], dict] = {
            row.get("driver_id"): {
                "total": int(row.get("total") or 0),
                "finished": int(row.get("finished") or 0),
                "in_progress": int(row.get("in_progress") or 0),
                "delayed": int(row.get("delayed") or 0),
                "without_deadline": int(row.get("without_deadline") or 0),
            }
            for row in sla_rows
        }

        by_driver: Dict[Optional[int], List[dict]] = {}
        global_status: Dict[tuple, dict] = {}
        total_travels = 0
        unassigned = 0

        for row in status_rows:
            uid = row.get("driver_id")
            quantity = int(row.get("quantity") or 0)
            total_travels += quantity
            if uid is None:
                unassigned += quantity
            by_driver.setdefault(uid, []).append(row)

            key = (
                int(row.get("status_id") or 0),
                row.get("status_type") or "SEM_STATUS",
                row.get("status_description"),
                bool(row.get("finished")),
            )
            if key not in global_status:
                global_status[key] = {
                    "status_id": key[0],
                    "status_type": key[1],
                    "status_description": key[2],
                    "finished": key[3],
                    "quantity": 0,
                }
            global_status[key]["quantity"] += quantity

        uids = [uid for uid in by_driver if uid is not None]
        names = await crud_lastmile_driver_metrics.get_driver_names(db, uids)

        drivers: List[DriverTravelStatusSummaryItemSC] = []
        for uid, rows in by_driver.items():
            driver_total = sum(int(row.get("quantity") or 0) for row in rows)
            profile = names.get(uid) if uid is not None else None
            sla_raw = sla_by_uid.get(
                uid,
                {
                    "total": driver_total,
                    "finished": 0,
                    "in_progress": driver_total,
                    "delayed": 0,
                    "without_deadline": 0,
                },
            )
            sla_raw["total"] = driver_total
            driver_name = (profile or {}).get("name")
            drivers.append(
                DriverTravelStatusSummaryItemSC(
                    driver_uid=uid,
                    driver_name=(driver_name or "").strip() or None,
                    cod_base=(profile or {}).get("cod_base"),
                    nome_unidade=(profile or {}).get("nome_unidade"),
                    total=driver_total,
                    by_status=self._to_status_list(rows),
                    sla=DriverTravelSlaSC(**sla_raw),
                )
            )

        drivers.sort(key=lambda item: (-item.total, item.driver_name or ""))

        return DriverTravelStatusSummarySC(
            date=filters.day,
            total_travels=total_travels,
            total_drivers=sum(1 for uid in by_driver if uid is not None),
            unassigned_travels=unassigned,
            by_status_global=self._to_status_list(list(global_status.values())),
            drivers=drivers,
        )


lastmile_driver_service = LastMileDriverService()
