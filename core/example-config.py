"""Renomeie este módulo para config.py (arquivo local, não versionado).

Valores abaixo são fictícios. Preencha host/usuário/senha no config.py local
ou via variáveis de ambiente. Nunca versionar secrets reais.
"""

import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings

from core.host_info import get_ip_suffix, get_local_ip

LOCAL_IP = get_local_ip()
IP_SUFFIX = get_ip_suffix(LOCAL_IP)


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    API_KEY_NAME: str = "access_token"
    DESCRIPTION: str = (
        "API de métricas LastMile (somente leitura) para dashboards do sistema Arancia."
    )

    DEBUG: bool = True

    if DEBUG:
        type_name: str = "homologacao"
        Pa_id: int = 24
        ROOT_PATH: str = "/hg-api-metrics"
        PROJECT_NAME: str = "Homologação Metrics API"
        ENABLE_TEST_ROUTES: bool = True
    else:
        type_name: str = "producao"
        Pa_id: int = 286
        ROOT_PATH: str = "/api-metrics"
        PROJECT_NAME: str = "Metrics API"
        ENABLE_TEST_ROUTES: bool = False

    LASTMILE_ORDER_TYPES: List[str] = [
        "LASTMILE",
        "LASTMILE_COLLECT",
        "LASTMILE_DELIVERY",
    ]
    # Visão LastMile por OS (ILIKE). Separado dos tipos de viagem acima.
    LASTMILE_OS_TYPE_PATTERNS: List[str] = [
        "LASTMILE_COLLECT",
        "LASTMILE_NORMAL",
        "LASTMILE_DESINSTAL%",
        "LASTMILE_RETIRADA%",
    ]
    # Carência da ociosidade do técnico (minutos sem abrir OS).
    LASTMILE_IDLE_GRACE_MINUTES: int = 50

    PSQL_HOST: str = "localhost"
    PSQL_USER: str = "user"
    PSQL_PASSWORD: str = "password"
    PSQL_DATABASE: str = "arancia_db"
    PSQL_PORT: int = 5432
    SQLALCHEMY_DATABASE_URI_PG: Optional[str] = None

    @validator("SQLALCHEMY_DATABASE_URI_PG", pre=True)
    def assemble_db_connection_psql(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str) and v:
            return v
        return (
            f'postgresql+asyncpg://{values.get("PSQL_USER")}:'
            f'{values.get("PSQL_PASSWORD")}@{values.get("PSQL_HOST")}:'
            f'{values.get("PSQL_PORT", 5432)}/{values.get("PSQL_DATABASE")}'
        )

    OTEL_ENABLED: bool = True
    OTEL_SERVICE_NAME: str = "MetricsAPI"
    OTEL_APPEND_ENV: bool = True
    OTEL_APPEND_IP_SUFFIX: bool = True
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://192.168.0.213:4318"
    OTEL_ENVIRONMENT: str = type_name
    OTEL_HOST_NAME: str = ""
    OTEL_DEFER_INIT: bool = False

    LOKI_ENABLED: bool = True
    LOKI_URL: str = "http://192.168.0.213:3100/loki/api/v1/push"
    LOKI_APP_NAME: str = "MetricsAPI"
    LOKI_HOST_NAME: str = ""
    LOKI_ASYNC: bool = True

    LOG_LEVEL: str = "INFO"

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_TIMEOUT: int = 10
    DB_POOL_RECYCLE: int = 1800

    @property
    def local_ip(self) -> str:
        return LOCAL_IP

    @property
    def name_suffix(self) -> str:
        parts: List[str] = []
        if self.OTEL_APPEND_ENV and self.OTEL_ENVIRONMENT:
            parts.append(self.OTEL_ENVIRONMENT)
        if self.OTEL_APPEND_IP_SUFFIX:
            parts.append(IP_SUFFIX)
        return ("-" + "-".join(parts)) if parts else ""

    @property
    def service_name(self) -> str:
        return f"{self.OTEL_SERVICE_NAME}{self.name_suffix}"

    @property
    def loki_app_name(self) -> str:
        return f"{self.LOKI_APP_NAME}{self.name_suffix}"

    @property
    def host_name(self) -> str:
        return self.OTEL_HOST_NAME or LOCAL_IP

    @property
    def loki_host_name(self) -> str:
        return self.LOKI_HOST_NAME or LOCAL_IP

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True


settings = Settings()
