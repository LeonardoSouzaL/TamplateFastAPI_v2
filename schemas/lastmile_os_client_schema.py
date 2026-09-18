from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class LastMileOsClientTravelStatusCountSC(BaseModel):
    status: str
    quantity: int = 0


class LastMileOsClientItemSC(BaseModel):
    client_id: Optional[int] = None
    cliente: Optional[str] = None
    chamado_count: int = 0
    sem_tecnico_count: int = 0
    atraso_count: int = 0
    dentro_do_prazo_count: int = 0
    sem_prazo_count: int = 0
    by_status_viagem: List[LastMileOsClientTravelStatusCountSC] = []


class LastMileOsClientOfensorSC(BaseModel):
    client_id: Optional[int] = None
    cliente: Optional[str] = None
    atraso_count: int = 0


class LastMileOsClientMelhorSC(BaseModel):
    client_id: Optional[int] = None
    cliente: Optional[str] = None
    dentro_do_prazo_count: int = 0


class LastMileOsClientResponseSC(BaseModel):
    vision: str = "LASTMILE"
    total: int = 0
    cliente_ofensor: Optional[LastMileOsClientOfensorSC] = None
    ofensores: List[LastMileOsClientOfensorSC] = []
    melhor_cliente: Optional[LastMileOsClientMelhorSC] = None
    melhores: List[LastMileOsClientMelhorSC] = []
    items: List[LastMileOsClientItemSC] = []


class LastMileOsClientFilters(BaseModel):
    """Filtros já resolvidos para o CRUD (sem regra de KPI)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type_mode: Literal["ilike", "in"] = "ilike"
    type_values: List[str]
    cliente_id: Optional[int] = None
    designation_id: Optional[int] = None
    data_inicial: Optional[datetime] = None
    data_final: Optional[datetime] = None
    now: datetime
