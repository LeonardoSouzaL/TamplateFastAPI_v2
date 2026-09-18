from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class LastMileOsOverviewResponseSC(BaseModel):
    vision: str = "LASTMILE"
    total: int = 0
    pendente_count: int = 0
    atendida_count: int = 0
    atendida_no_prazo_count: int = 0
    fora_do_prazo_count: int = 0
    sem_tecnico_count: int = 0
    atendida_no_prazo_percent: float = 0.0
    fora_do_prazo_percent: float = 0.0
    efetividade_percent: float = 0.0


class LastMileOsOverviewFilters(BaseModel):
    """Filtros já resolvidos para o CRUD (sem regra de KPI)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type_mode: Literal["ilike", "in"] = "ilike"
    type_values: List[str]
    cliente_id: Optional[int] = None
    designation_id: Optional[int] = None
    data_inicial: Optional[datetime] = None
    data_final: Optional[datetime] = None
    now: datetime
