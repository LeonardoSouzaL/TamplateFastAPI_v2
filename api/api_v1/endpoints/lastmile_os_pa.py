from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Query

from api.deps import DbDep
from schemas.lastmile_os_pa_schema import LastMileOsPaResponseSC
from services.lastmile_os_pa_service import lastmile_os_pa_service

router = APIRouter()


@router.get(
    "/orders/by-pa",
    response_model=LastMileOsPaResponseSC,
    summary="Totais de OS LastMile agrupados por PA (designacao)",
)
async def lastmile_os_by_pa(
    db: DbDep,
    order_type: Optional[str] = Query(
        None,
        description=(
            "CSV de tipos. Omitido = visão LastMile OS "
            "(COLLECT, NORMAL, DESINSTAL%, RETIRADA%). CSV vazio = totais 0."
        ),
    ),
    cliente_id: Optional[int] = None,
    designation_id: Optional[int] = Query(
        None,
        description="PA da OS (service_order.designation_id).",
    ),
    data_inicial: Optional[datetime] = Query(
        None,
        description="Início do intervalo em service_order.created_at (inclusive).",
    ),
    data_final: Optional[datetime] = Query(
        None,
        description="Fim do intervalo em service_order.created_at (inclusive).",
    ),
) -> Any:
    return await lastmile_os_pa_service.get_by_pa(
        db=db,
        order_type=order_type,
        cliente_id=cliente_id,
        designation_id=designation_id,
        data_inicial=data_inicial,
        data_final=data_final,
    )
