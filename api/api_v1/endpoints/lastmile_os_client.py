from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Query

from api.deps import DbDep
from schemas.lastmile_os_client_schema import LastMileOsClientResponseSC
from services.lastmile_os_client_service import lastmile_os_client_service

router = APIRouter()


@router.get(
    "/orders/by-client",
    response_model=LastMileOsClientResponseSC,
    summary="Totais de OS LastMile agrupados por cliente",
)
async def lastmile_os_by_client(
    db: DbDep,
    order_type: Optional[str] = Query(
        None,
        description=(
            "CSV de tipos. Omitido = visão LastMile OS "
            "(COLLECT, NORMAL, DESINSTAL%, RETIRADA%). CSV vazio = totais 0."
        ),
    ),
    cliente_id: Optional[int] = Query(
        None,
        description="Cliente da OS (service_order.client_id).",
    ),
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
    return await lastmile_os_client_service.get_by_client(
        db=db,
        order_type=order_type,
        cliente_id=cliente_id,
        designation_id=designation_id,
        data_inicial=data_inicial,
        data_final=data_final,
    )
