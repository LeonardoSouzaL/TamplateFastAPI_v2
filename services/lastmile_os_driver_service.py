from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional, Tuple, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from crud.crud_lastmile_os_driver_metrics import crud_lastmile_os_driver_metrics
from schemas.lastmile_os_driver_schema import (
    LastMileOsDriverFilters,
    LastMileOsDriverItemSC,
    LastMileOsDriverMelhorSC,
    LastMileOsDriverOciosoSC,
    LastMileOsDriverOfensorSC,
    LastMileOsDriverResponseSC,
    LastMileOsDriverTravelStatusCountSC,
)
from services.lastmile_os_status_service import VISION, resolve_type_filter

TOP_N = 10
RankItem = TypeVar("RankItem")


def _empty_response() -> LastMileOsDriverResponseSC:
    return LastMileOsDriverResponseSC(vision=VISION, total=0, items=[])


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def compute_driver_idle(
    *,
    last_opening: Optional[datetime],
    rota_atribuida: bool,
    now: datetime,
    grace_minutes: Optional[int] = None,
) -> Tuple[bool, int]:
    """Ociosidade: porta de rota hoje + carência. Sem rota ou last_opening nulo = 0."""
    if not rota_atribuida or last_opening is None:
        return False, 0

    grace = timedelta(
        minutes=grace_minutes
        if grace_minutes is not None
        else settings.LASTMILE_IDLE_GRACE_MINUTES
    )
    elapsed = _aware(now) - _aware(last_opening)
    if elapsed <= grace:
        return False, 0
    return True, int((elapsed - grace).total_seconds())


def _top_rank(
    items: List[LastMileOsDriverItemSC],
    *,
    count_of: Callable[[LastMileOsDriverItemSC], int],
    build: Callable[[LastMileOsDriverItemSC], RankItem],
    limit: int = TOP_N,
) -> List[RankItem]:
    ranked = [item for item in items if count_of(item) > 0]
    ranked.sort(key=lambda item: (-count_of(item), -(item.driver_uid or 0)))
    return [build(item) for item in ranked[:limit]]


def _ofensores(items: List[LastMileOsDriverItemSC]) -> List[LastMileOsDriverOfensorSC]:
    return _top_rank(
        items,
        count_of=lambda item: item.atraso_count,
        build=lambda item: LastMileOsDriverOfensorSC(
            driver_uid=item.driver_uid,
            tecnico=item.tecnico,
            atraso_count=item.atraso_count,
        ),
    )


def _melhores(items: List[LastMileOsDriverItemSC]) -> List[LastMileOsDriverMelhorSC]:
    return _top_rank(
        items,
        count_of=lambda item: item.dentro_do_prazo_count,
        build=lambda item: LastMileOsDriverMelhorSC(
            driver_uid=item.driver_uid,
            tecnico=item.tecnico,
            dentro_do_prazo_count=item.dentro_do_prazo_count,
        ),
    )


def _ociosos(items: List[LastMileOsDriverItemSC]) -> List[LastMileOsDriverOciosoSC]:
    ranked = [
        item
        for item in items
        if item.ocioso and item.ociosidade_segundos > 0
    ]
    ranked.sort(
        key=lambda item: (-item.ociosidade_segundos, -(item.driver_uid or 0))
    )
    return [
        LastMileOsDriverOciosoSC(
            driver_uid=item.driver_uid,
            tecnico=item.tecnico,
            ociosidade_segundos=item.ociosidade_segundos,
        )
        for item in ranked[:TOP_N]
    ]


class LastMileOsDriverService:
    async def get_by_driver(
        self,
        *,
        db: AsyncSession,
        order_type: Optional[str] = None,
        cliente_id: Optional[int] = None,
        designation_id: Optional[int] = None,
        driver_id: Optional[int] = None,
        data_inicial: Optional[datetime] = None,
        data_final: Optional[datetime] = None,
    ) -> LastMileOsDriverResponseSC:
        type_filter = resolve_type_filter(order_type)
        if type_filter is None:
            return _empty_response()

        type_mode, type_values = type_filter
        filters = LastMileOsDriverFilters(
            type_mode=type_mode,
            type_values=type_values,
            cliente_id=cliente_id,
            designation_id=designation_id,
            driver_id=driver_id,
            data_inicial=data_inicial,
            data_final=data_final,
            now=datetime.now(timezone.utc),
        )

        rows = await crud_lastmile_os_driver_metrics.aggregate_by_driver(
            db=db,
            filters=filters,
        )
        status_rows = (
            await crud_lastmile_os_driver_metrics.aggregate_travel_status_by_driver(
                db=db,
                filters=filters,
            )
        )

        status_by_driver: Dict[
            Optional[int], List[LastMileOsDriverTravelStatusCountSC]
        ] = {}
        for row in status_rows:
            quantity = int(row.get("quantity") or 0)
            if not quantity:
                continue
            uid = row.get("driver_id")
            status_name = str(row.get("status") or "")
            status_by_driver.setdefault(uid, []).append(
                LastMileOsDriverTravelStatusCountSC(
                    status=status_name, quantity=quantity
                )
            )
        for status_items in status_by_driver.values():
            status_items.sort(key=lambda item: (-item.quantity, item.status))

        sem_tecnico_count = 0
        assigned_rows: List[dict] = []
        for row in rows:
            if row.get("driver_id") is None:
                sem_tecnico_count += int(row.get("chamado_count") or 0)
                continue
            assigned_rows.append(row)

        uids = [row.get("driver_id") for row in assigned_rows]
        profiles = await crud_lastmile_os_driver_metrics.get_driver_profiles(
            db, uids
        )
        with_route = (
            await crud_lastmile_os_driver_metrics.list_drivers_with_route_today(
                db=db,
                filters=filters,
                uids=uids,
            )
        )

        items: List[LastMileOsDriverItemSC] = []
        assigned_total = 0
        for row in assigned_rows:
            uid = row.get("driver_id")
            chamado_count = int(row.get("chamado_count") or 0)
            assigned_total += chamado_count
            profile = profiles.get(uid) or {}
            last_opening = profile.get("last_opening")
            rota_atribuida = uid in with_route
            ocioso, ociosidade_segundos = compute_driver_idle(
                last_opening=last_opening,
                rota_atribuida=rota_atribuida,
                now=filters.now,
            )
            driver_name = (profile.get("name") or "").strip() or None
            items.append(
                LastMileOsDriverItemSC(
                    driver_uid=uid,
                    tecnico=driver_name,
                    cod_base=profile.get("cod_base"),
                    nome_unidade=profile.get("nome_unidade"),
                    chamado_count=chamado_count,
                    atraso_count=int(row.get("atraso") or 0),
                    dentro_do_prazo_count=int(row.get("dentro_do_prazo") or 0),
                    sem_prazo_count=int(row.get("sem_prazo") or 0),
                    rota_atribuida=rota_atribuida,
                    last_opening=last_opening,
                    ocioso=ocioso,
                    ociosidade_segundos=ociosidade_segundos,
                    by_status_viagem=status_by_driver.get(uid, []),
                )
            )

        items.sort(key=lambda item: (-item.chamado_count, item.driver_uid or 0))
        ofensores = _ofensores(items)
        melhores = _melhores(items)
        ociosos = _ociosos(items)
        return LastMileOsDriverResponseSC(
            vision=VISION,
            total=assigned_total + sem_tecnico_count,
            sem_tecnico_count=sem_tecnico_count,
            tecnico_ofensor=ofensores[0] if ofensores else None,
            ofensores=ofensores,
            melhor_tecnico=melhores[0] if melhores else None,
            melhores=melhores,
            tecnico_ocioso=ociosos[0] if ociosos else None,
            ociosos=ociosos,
            items=items,
        )


lastmile_os_driver_service = LastMileOsDriverService()
