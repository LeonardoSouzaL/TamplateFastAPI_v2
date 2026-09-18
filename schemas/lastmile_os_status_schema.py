from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class LastMileOsStatusCountSC(BaseModel):
    status: str
    finished: bool = False
    quantity: int = 0


class LastMileOsTypeCountSC(BaseModel):
    order_type: str
    quantity: int = 0


class LastMileOsStatusResponseSC(BaseModel):
    vision: str = "LASTMILE"
    status_filter: List[str] = []
    finished_filter: Optional[bool] = None
    total: int = 0
    universe_total: int = 0
    by_status: List[LastMileOsStatusCountSC] = []
    by_order_type: List[LastMileOsTypeCountSC] = []


class LastMileOsStatusFilters(BaseModel):
    """Filtros já resolvidos para o CRUD (sem regra de KPI)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type_mode: Literal["ilike", "in"] = "ilike"
    type_values: List[str]
    status_types: List[str] = []
    finished: Optional[bool] = None
    cliente_id: Optional[int] = None
    designation_id: Optional[int] = None
    data_inicial: Optional[datetime] = None
    data_final: Optional[datetime] = None
