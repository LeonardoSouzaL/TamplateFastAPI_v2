from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Query

from api.deps import DbDep
from schemas.lastmile_os_status_schema import LastMileOsStatusResponseSC
from services.lastmile_os_status_service import lastmile_os_status_service

router = APIRouter()


@router.get(
    "/orders/by-status",
    response_model=LastMileOsStatusResponseSC,
    summary="Totais de OS LastMile por status da ordem",
)
async def lastmile_os_by_status(
    db: DbDep,
    status: Optional[str] = Query(
        None,
        description="CSV de status (case-insensitive). PENDING une Pending e PENDING.",
    ),
    finished: Optional[bool] = Query(
        None,
        description="true = finalizador; false = não finalizador. Omitido = ambos.",
    ),
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
    return await lastmile_os_status_service.get_by_status(
        db=db,
        status=status,
        finished=finished,
        order_type=order_type,
        cliente_id=cliente_id,
        designation_id=designation_id,
        data_inicial=data_inicial,
        data_final=data_final,
    )
