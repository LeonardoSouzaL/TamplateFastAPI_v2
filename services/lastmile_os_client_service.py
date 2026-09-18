from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_lastmile_metrics import crud_lastmile_metrics
from crud.crud_lastmile_os_client_metrics import crud_lastmile_os_client_metrics
from schemas.lastmile_os_client_schema import (
    LastMileOsClientFilters,
    LastMileOsClientItemSC,
    LastMileOsClientMelhorSC,
    LastMileOsClientOfensorSC,
    LastMileOsClientResponseSC,
    LastMileOsClientTravelStatusCountSC,
)
from services.lastmile_os_status_service import VISION, resolve_type_filter

TOP_N = 10
RankItem = TypeVar("RankItem")


def _empty_response() -> LastMileOsClientResponseSC:
    return LastMileOsClientResponseSC(vision=VISION, total=0, items=[])


def _top_rank(
    items: List[LastMileOsClientItemSC],
    *,
    count_of: Callable[[LastMileOsClientItemSC], int],
    build: Callable[[LastMileOsClientItemSC], RankItem],
    limit: int = TOP_N,
) -> List[RankItem]:
    ranked = [item for item in items if count_of(item) > 0]
    ranked.sort(key=lambda item: (-count_of(item), -(item.client_id or 0)))
    return [build(item) for item in ranked[:limit]]


def _ofensores(items: List[LastMileOsClientItemSC]) -> List[LastMileOsClientOfensorSC]:
    return _top_rank(
        items,
        count_of=lambda item: item.atraso_count,
        build=lambda item: LastMileOsClientOfensorSC(
            client_id=item.client_id,
            cliente=item.cliente,
            atraso_count=item.atraso_count,
        ),
    )


def _melhores(items: List[LastMileOsClientItemSC]) -> List[LastMileOsClientMelhorSC]:
    return _top_rank(
        items,
        count_of=lambda item: item.dentro_do_prazo_count,
        build=lambda item: LastMileOsClientMelhorSC(
            client_id=item.client_id,
            cliente=item.cliente,
            dentro_do_prazo_count=item.dentro_do_prazo_count,
        ),
    )


class LastMileOsClientService:
    async def get_by_client(
        self,
        *,
        db: AsyncSession,
        order_type: Optional[str] = None,
        cliente_id: Optional[int] = None,
        designation_id: Optional[int] = None,
        data_inicial: Optional[datetime] = None,
        data_final: Optional[datetime] = None,
    ) -> LastMileOsClientResponseSC:
        type_filter = resolve_type_filter(order_type)
        if type_filter is None:
            return _empty_response()

        type_mode, type_values = type_filter
        filters = LastMileOsClientFilters(
            type_mode=type_mode,
            type_values=type_values,
            cliente_id=cliente_id,
            designation_id=designation_id,
            data_inicial=data_inicial,
            data_final=data_final,
            now=datetime.now(timezone.utc),
        )

        rows = await crud_lastmile_os_client_metrics.aggregate_by_client(
            db=db,
            filters=filters,
        )
        status_rows = (
            await crud_lastmile_os_client_metrics.aggregate_travel_status_by_client(
                db=db,
                filters=filters,
            )
        )

        status_by_client: Dict[
            Optional[int], List[LastMileOsClientTravelStatusCountSC]
        ] = {}
        for row in status_rows:
            quantity = int(row.get("quantity") or 0)
            if not quantity:
                continue
            client_id = row.get("client_id")
            status_name = str(row.get("status") or "")
            status_by_client.setdefault(client_id, []).append(
                LastMileOsClientTravelStatusCountSC(
                    status=status_name, quantity=quantity
                )
            )
        for status_items in status_by_client.values():
            status_items.sort(key=lambda item: (-item.quantity, item.status))

        client_ids = [
            row.get("client_id") for row in rows if row.get("client_id") is not None
        ]
        names = await crud_lastmile_metrics.get_location_names(db, client_ids)

        items: List[LastMileOsClientItemSC] = []
        total = 0
        for row in rows:
            client_id = row.get("client_id")
            chamado_count = int(row.get("chamado_count") or 0)
            total += chamado_count
            items.append(
                LastMileOsClientItemSC(
                    client_id=client_id,
                    cliente=names.get(client_id) if client_id is not None else None,
                    chamado_count=chamado_count,
                    sem_tecnico_count=int(row.get("sem_tecnico") or 0),
                    atraso_count=int(row.get("atraso") or 0),
                    dentro_do_prazo_count=int(row.get("dentro_do_prazo") or 0),
                    sem_prazo_count=int(row.get("sem_prazo") or 0),
                    by_status_viagem=status_by_client.get(client_id, []),
                )
            )

        items.sort(key=lambda item: (-item.chamado_count, item.client_id or 0))
        ofensores = _ofensores(items)
        melhores = _melhores(items)
        return LastMileOsClientResponseSC(
            vision=VISION,
            total=total,
            cliente_ofensor=ofensores[0] if ofensores else None,
            ofensores=ofensores,
            melhor_cliente=melhores[0] if melhores else None,
            melhores=melhores,
            items=items,
        )


lastmile_os_client_service = LastMileOsClientService()
