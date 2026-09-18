from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Query

from api.deps import DbDep
from schemas.lastmile_dashboard_schema import (
    DriverTravelStatusSummarySC,
    PaTravelDashboardSC,
    TravelMetricResponseSC,
    TravelMetricType,
)
from services.lastmile_dashboard_service import lastmile_dashboard_service
from services.lastmile_driver_service import lastmile_driver_service

router = APIRouter()


@router.get(
    "/dashboard/pa-summary",
    response_model=PaTravelDashboardSC,
    summary="Dashboard LastMile agrupado por PA (designation)",
)
async def dashboard_pa_summary(
    db: DbDep,
    data_inicial: Optional[datetime] = None,
    data_final: Optional[datetime] = None,
    designation_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    carrier_id: Optional[int] = None,
    cliente_id: Optional[int] = None,
    order_type: Optional[str] = Query(
        None,
        description="CSV de tipos. Omitido = LASTMILE,LASTMILE_COLLECT,LASTMILE_DELIVERY.",
    ),
    only_pending: Optional[bool] = None,
    only_without_driver: Optional[bool] = None,
    only_late: Optional[bool] = None,
) -> Any:
    return await lastmile_dashboard_service.get_pa_summary(
        db=db,
        data_inicial=data_inicial,
        data_final=data_final,
        designation_id=designation_id,
        driver_id=driver_id,
        carrier_id=carrier_id,
        cliente_id=cliente_id,
        order_type=order_type,
        only_pending=only_pending,
        only_without_driver=only_without_driver,
        only_late=only_late,
    )


@router.get(
    "/dashboard/metrics",
    response_model=TravelMetricResponseSC,
    summary="KPI LastMile (quantidade única com breakdown opcional)",
)
async def dashboard_metrics(
    db: DbDep,
    metric: TravelMetricType = Query(
        ...,
        description="pending | without_driver | finished | worst_late_pa",
    ),
    data_inicial: Optional[datetime] = None,
    data_final: Optional[datetime] = None,
    designation_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    carrier_id: Optional[int] = None,
    cliente_id: Optional[int] = None,
    order_type: Optional[str] = Query(
        None,
        description="CSV de tipos. Omitido = LASTMILE,LASTMILE_COLLECT,LASTMILE_DELIVERY.",
    ),
    group_by_client: Optional[bool] = Query(
        False,
        description="Quando True, inclui breakdown por cliente (exceto worst_late_pa, que quebra por PA).",
    ),
    group_by_order_type: Optional[bool] = Query(
        False,
        description="Quando True, inclui breakdown por tipo de serviço (exceto worst_late_pa, que quebra por PA).",
    ),
) -> Any:
    return await lastmile_dashboard_service.get_metric(
        db=db,
        metric=metric,
        data_inicial=data_inicial,
        data_final=data_final,
        designation_id=designation_id,
        driver_id=driver_id,
        carrier_id=carrier_id,
        cliente_id=cliente_id,
        order_type=order_type,
        group_by_client=bool(group_by_client),
        group_by_order_type=bool(group_by_order_type),
    )


@router.get(
    "/dashboard/driver-status-summary",
    response_model=DriverTravelStatusSummarySC,
    summary="Dashboard LastMile de viagens do dia por técnico e status",
)
async def dashboard_driver_status_summary(
    db: DbDep,
    created_at: Optional[date] = Query(
        None,
        description="Dia da rota em America/Sao_Paulo. Omitido = hoje.",
    ),
    designation_id: Optional[int] = Query(
        None,
        description="PA da viagem (order_travels.designation_id).",
    ),
    driver_id: Optional[int] = Query(
        None,
        description="UID do técnico (order_travels.driver_id).",
    ),
    carrier_id: Optional[int] = None,
    cliente_id: Optional[int] = None,
    order_type: Optional[str] = Query(
        None,
        description="CSV de tipos. Omitido = LASTMILE,LASTMILE_COLLECT,LASTMILE_DELIVERY.",
    ),
) -> Any:
    return await lastmile_driver_service.get_driver_status_summary(
        db=db,
        created_at=created_at,
        designation_id=designation_id,
        driver_id=driver_id,
        carrier_id=carrier_id,
        cliente_id=cliente_id,
        order_type=order_type,
    )
