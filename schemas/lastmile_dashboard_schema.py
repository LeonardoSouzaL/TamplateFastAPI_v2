from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TravelMetricType(str, Enum):
    pending = "pending"
    without_driver = "without_driver"
    finished = "finished"
    worst_late_pa = "worst_late_pa"


class PaCountSC(BaseModel):
    pa_id: Optional[int] = None
    pa_name: Optional[str] = None
    quantity: int = 0


class PaLateCountSC(BaseModel):
    pa_id: Optional[int] = None
    pa_name: Optional[str] = None
    late_count: int = 0


class PaAverageServiceTimeSC(BaseModel):
    pa_id: Optional[int] = None
    pa_name: Optional[str] = None
    average_minutes: int = 0
    average_formatted: str = "00:00"


class PaTravelDashboardSC(BaseModel):
    total_pending: int = 0
    total_without_driver: int = 0
    total_finished: int = 0
    worst_sla_pa: Optional[PaLateCountSC] = None
    pending_by_pa: List[PaCountSC] = []
    without_driver_by_pa: List[PaCountSC] = []
    finished_by_pa: List[PaCountSC] = []
    average_service_time_by_pa: List[PaAverageServiceTimeSC] = []
    late_by_pa: List[PaLateCountSC] = []


class TravelMetricBreakdownSC(BaseModel):
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    order_type: Optional[str] = None
    pa_id: Optional[int] = None
    pa_name: Optional[str] = None
    quantity: int = 0


class TravelMetricResponseSC(BaseModel):
    metric: TravelMetricType
    quantity: int = 0
    breakdown: List[TravelMetricBreakdownSC] = []


class TravelStatusCountSC(BaseModel):
    status_id: int
    status_type: str
    status_description: Optional[str] = None
    finished: bool = False
    count: int


class DriverTravelSlaSC(BaseModel):
    total: int
    finished: int
    in_progress: int
    delayed: int
    without_deadline: int


class DriverTravelStatusSummaryItemSC(BaseModel):
    driver_uid: Optional[int] = None
    driver_name: Optional[str] = None
    cod_base: Optional[str] = None
    nome_unidade: Optional[str] = None
    total: int
    by_status: List[TravelStatusCountSC]
    sla: DriverTravelSlaSC


class DriverTravelStatusSummarySC(BaseModel):
    """Totais de viagens LastMile do dia por técnico e status."""

    date: date
    total_travels: int
    total_drivers: int
    unassigned_travels: int
    by_status_global: List[TravelStatusCountSC]
    drivers: List[DriverTravelStatusSummaryItemSC]


class LastMileDashboardFilters(BaseModel):
    """Filtros já resolvidos para o CRUD (sem regra de KPI)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    order_types: List[str]
    data_inicial: Optional[datetime] = None
    data_final: Optional[datetime] = None
    designation_id: Optional[int] = None
    driver_id: Optional[int] = None
    carrier_id: Optional[int] = None
    cliente_id: Optional[int] = None
    apenas_nao_finalizada: bool = False
    apenas_finalizada: bool = False
    sem_motorista: bool = False
    only_late: Optional[bool] = None
    now: datetime


class LastMileDriverFilters(BaseModel):
    """Filtros já resolvidos para o CRUD de técnico (sem regra de KPI)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    order_types: List[str]
    day: date
    designation_id: Optional[int] = None
    driver_id: Optional[int] = None
    carrier_id: Optional[int] = None
    cliente_id: Optional[int] = None
    now: datetime
