from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class LastMileOsDriverTravelStatusCountSC(BaseModel):
    status: str
    quantity: int = 0


class LastMileOsDriverItemSC(BaseModel):
    driver_uid: Optional[int] = None
    tecnico: Optional[str] = None
    cod_base: Optional[str] = None
    nome_unidade: Optional[str] = None
    chamado_count: int = 0
    atraso_count: int = 0
    dentro_do_prazo_count: int = 0
    sem_prazo_count: int = 0
    rota_atribuida: bool = False
    last_opening: Optional[datetime] = None
    ocioso: bool = False
    ociosidade_segundos: int = 0
    by_status_viagem: List[LastMileOsDriverTravelStatusCountSC] = []


class LastMileOsDriverOfensorSC(BaseModel):
    driver_uid: Optional[int] = None
    tecnico: Optional[str] = None
    atraso_count: int = 0


class LastMileOsDriverMelhorSC(BaseModel):
    driver_uid: Optional[int] = None
    tecnico: Optional[str] = None
    dentro_do_prazo_count: int = 0


class LastMileOsDriverOciosoSC(BaseModel):
    driver_uid: Optional[int] = None
    tecnico: Optional[str] = None
    ociosidade_segundos: int = 0


class LastMileOsDriverResponseSC(BaseModel):
    vision: str = "LASTMILE"
    total: int = 0
    sem_tecnico_count: int = 0
    tecnico_ofensor: Optional[LastMileOsDriverOfensorSC] = None
    ofensores: List[LastMileOsDriverOfensorSC] = []
    melhor_tecnico: Optional[LastMileOsDriverMelhorSC] = None
    melhores: List[LastMileOsDriverMelhorSC] = []
    tecnico_ocioso: Optional[LastMileOsDriverOciosoSC] = None
    ociosos: List[LastMileOsDriverOciosoSC] = []
    items: List[LastMileOsDriverItemSC] = []


class LastMileOsDriverFilters(BaseModel):
    """Filtros já resolvidos para o CRUD (sem regra de KPI)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type_mode: Literal["ilike", "in"] = "ilike"
    type_values: List[str]
    cliente_id: Optional[int] = None
    designation_id: Optional[int] = None
    driver_id: Optional[int] = None
    data_inicial: Optional[datetime] = None
    data_final: Optional[datetime] = None
    now: datetime
