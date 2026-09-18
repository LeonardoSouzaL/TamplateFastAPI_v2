from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_lastmile_metrics import crud_lastmile_metrics
from crud.crud_lastmile_os_pa_metrics import crud_lastmile_os_pa_metrics
from schemas.lastmile_os_pa_schema import (
    LastMileOsPaFilters,
    LastMileOsPaItemSC,
    LastMileOsPaMelhorSC,
    LastMileOsPaOfensoraSC,
    LastMileOsPaResponseSC,
    LastMileOsTravelStatusCountSC,
)
from services.lastmile_os_status_service import VISION, resolve_type_filter

TOP_N = 10
RankItem = TypeVar("RankItem")


def _empty_response() -> LastMileOsPaResponseSC:
    return LastMileOsPaResponseSC(vision=VISION, total=0, items=[])


def _top_rank(
    items: List[LastMileOsPaItemSC],
    *,
    count_of: Callable[[LastMileOsPaItemSC], int],
    build: Callable[[LastMileOsPaItemSC], RankItem],
    limit: int = TOP_N,
) -> List[RankItem]:
    ranked = [item for item in items if count_of(item) > 0]
    ranked.sort(key=lambda item: (-count_of(item), -(item.pa_id or 0)))
    return [build(item) for item in ranked[:limit]]


def _ofensoras(items: List[LastMileOsPaItemSC]) -> List[LastMileOsPaOfensoraSC]:
    return _top_rank(
        items,
        count_of=lambda item: item.atraso_count,
        build=lambda item: LastMileOsPaOfensoraSC(
            pa_id=item.pa_id,
            designacao=item.designacao,
            atraso_count=item.atraso_count,
        ),
    )


def _melhores(items: List[LastMileOsPaItemSC]) -> List[LastMileOsPaMelhorSC]:
    return _top_rank(
        items,
        count_of=lambda item: item.dentro_do_prazo_count,
        build=lambda item: LastMileOsPaMelhorSC(
            pa_id=item.pa_id,
            designacao=item.designacao,
            dentro_do_prazo_count=item.dentro_do_prazo_count,
        ),
    )


class LastMileOsPaService:
    async def get_by_pa(
        self,
        *,
        db: AsyncSession,
        order_type: Optional[str] = None,
        cliente_id: Optional[int] = None,
        designation_id: Optional[int] = None,
        data_inicial: Optional[datetime] = None,
        data_final: Optional[datetime] = None,
    ) -> LastMileOsPaResponseSC:
        type_filter = resolve_type_filter(order_type)
        if type_filter is None:
            return _empty_response()

        type_mode, type_values = type_filter
        filters = LastMileOsPaFilters(
            type_mode=type_mode,
            type_values=type_values,
            cliente_id=cliente_id,
            designation_id=designation_id,
            data_inicial=data_inicial,
            data_final=data_final,
            now=datetime.now(timezone.utc),
        )

        rows = await crud_lastmile_os_pa_metrics.aggregate_by_pa(
            db=db,
            filters=filters,
        )
        status_rows = await crud_lastmile_os_pa_metrics.aggregate_travel_status_by_pa(
            db=db,
            filters=filters,
        )

        status_by_pa: Dict[Optional[int], List[LastMileOsTravelStatusCountSC]] = {}
        for row in status_rows:
            quantity = int(row.get("quantity") or 0)
            if not quantity:
                continue
            pa_id = row.get("pa_id")
            status_name = str(row.get("status") or "")
            status_by_pa.setdefault(pa_id, []).append(
                LastMileOsTravelStatusCountSC(status=status_name, quantity=quantity)
            )
        for status_items in status_by_pa.values():
            status_items.sort(key=lambda item: (-item.quantity, item.status))

        pa_ids = [row.get("pa_id") for row in rows if row.get("pa_id") is not None]
        names = await crud_lastmile_metrics.get_location_names(db, pa_ids)

        items: List[LastMileOsPaItemSC] = []
        total = 0
        for row in rows:
            pa_id = row.get("pa_id")
            chamado_count = int(row.get("chamado_count") or 0)
            total += chamado_count
            items.append(
                LastMileOsPaItemSC(
                    pa_id=pa_id,
                    designacao=names.get(pa_id) if pa_id is not None else None,
                    chamado_count=chamado_count,
                    sem_tecnico_count=int(row.get("sem_tecnico") or 0),
                    atraso_count=int(row.get("atraso") or 0),
                    dentro_do_prazo_count=int(row.get("dentro_do_prazo") or 0),
                    sem_prazo_count=int(row.get("sem_prazo") or 0),
                    by_status_viagem=status_by_pa.get(pa_id, []),
                )
            )

        items.sort(key=lambda item: (-item.chamado_count, item.pa_id or 0))
        ofensoras = _ofensoras(items)
        melhores = _melhores(items)
        return LastMileOsPaResponseSC(
            vision=VISION,
            total=total,
            pa_ofensora=ofensoras[0] if ofensoras else None,
            ofensoras=ofensoras,
            melhor_pa=melhores[0] if melhores else None,
            melhores=melhores,
            items=items,
        )


lastmile_os_pa_service = LastMileOsPaService()
