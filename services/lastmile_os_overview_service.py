from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_lastmile_os_overview_metrics import crud_lastmile_os_overview_metrics
from schemas.lastmile_os_overview_schema import (
    LastMileOsOverviewFilters,
    LastMileOsOverviewResponseSC,
)
from services.lastmile_os_status_service import VISION, resolve_type_filter


def _percent(part: int, whole: int) -> float:
    if whole <= 0:
        return 0.0
    return round(part / whole * 100, 2)


def _empty_response() -> LastMileOsOverviewResponseSC:
    return LastMileOsOverviewResponseSC(vision=VISION)


class LastMileOsOverviewService:
    async def get_overview(
        self,
        *,
        db: AsyncSession,
        order_type: Optional[str] = None,
        cliente_id: Optional[int] = None,
        designation_id: Optional[int] = None,
        data_inicial: Optional[datetime] = None,
        data_final: Optional[datetime] = None,
    ) -> LastMileOsOverviewResponseSC:
        type_filter = resolve_type_filter(order_type)
        if type_filter is None:
            return _empty_response()

        type_mode, type_values = type_filter
        filters = LastMileOsOverviewFilters(
            type_mode=type_mode,
            type_values=type_values,
            cliente_id=cliente_id,
            designation_id=designation_id,
            data_inicial=data_inicial,
            data_final=data_final,
            now=datetime.now(timezone.utc),
        )
        row = await crud_lastmile_os_overview_metrics.aggregate_overview(
            db=db,
            filters=filters,
        )
        total = int(row.get("total") or 0)
        pendente_count = int(row.get("pendente") or 0)
        atendida_count = int(row.get("atendida") or 0)
        atendida_no_prazo_count = int(row.get("atendida_no_prazo") or 0)
        fora_do_prazo_count = int(row.get("atraso") or 0)
        sem_tecnico_count = int(row.get("sem_tecnico") or 0)
        return LastMileOsOverviewResponseSC(
            vision=VISION,
            total=total,
            pendente_count=pendente_count,
            atendida_count=atendida_count,
            atendida_no_prazo_count=atendida_no_prazo_count,
            fora_do_prazo_count=fora_do_prazo_count,
            sem_tecnico_count=sem_tecnico_count,
            atendida_no_prazo_percent=_percent(atendida_no_prazo_count, total),
            fora_do_prazo_percent=_percent(fora_do_prazo_count, total),
            efetividade_percent=_percent(
                atendida_no_prazo_count,
                atendida_no_prazo_count + fora_do_prazo_count,
            ),
        )


lastmile_os_overview_service = LastMileOsOverviewService()
