from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class LastMileOsTravelStatusCountSC(BaseModel):
    status: str
    quantity: int = 0


class LastMileOsPaItemSC(BaseModel):
    pa_id: Optional[int] = None
    designacao: Optional[str] = None
    chamado_count: int = 0
    sem_tecnico_count: int = 0
    atraso_count: int = 0
    dentro_do_prazo_count: int = 0
    sem_prazo_count: int = 0
    by_status_viagem: List[LastMileOsTravelStatusCountSC] = []


class LastMileOsPaOfensoraSC(BaseModel):
    pa_id: Optional[int] = None
    designacao: Optional[str] = None
    atraso_count: int = 0


class LastMileOsPaMelhorSC(BaseModel):
    pa_id: Optional[int] = None
    designacao: Optional[str] = None
    dentro_do_prazo_count: int = 0


class LastMileOsPaResponseSC(BaseModel):
    vision: str = "LASTMILE"
    total: int = 0
    pa_ofensora: Optional[LastMileOsPaOfensoraSC] = None
    ofensoras: List[LastMileOsPaOfensoraSC] = []
    melhor_pa: Optional[LastMileOsPaMelhorSC] = None
    melhores: List[LastMileOsPaMelhorSC] = []
    items: List[LastMileOsPaItemSC] = []


class LastMileOsPaFilters(BaseModel):
    """Filtros já resolvidos para o CRUD (sem regra de KPI)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type_mode: Literal["ilike", "in"] = "ilike"
    type_values: List[str]
    cliente_id: Optional[int] = None
    designation_id: Optional[int] = None
    data_inicial: Optional[datetime] = None
    data_final: Optional[datetime] = None
    now: datetime
