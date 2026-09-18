"""Configuração base de OpenTelemetry (traces) para a Metrics API.

Envia traces via OTLP HTTP ao Grafana Tempo (porta 4318) e correlaciona logs
por `trace_id`/`span_id`. Toda a config vem de `settings` (core/config.py).
O startup não pode quebrar se o Tempo/Loki estiverem indisponíveis.
"""

import logging

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from core.config import settings
from core.logging_config import LOG_FORMAT

logger = logging.getLogger(__name__)

_engines_instrumentados: set[int] = set()
_clients_instrumentados = False


def setup_logging_instrumentation() -> None:
    LoggingInstrumentor().instrument(
        set_logging_format=True,
        logging_format=LOG_FORMAT,
    )


def setup_base_telemetry() -> None:
    """Deve rodar ANTES de setup_logging_instrumentation() para que o
    service.name (do resource) seja capturado pelo record factory dos logs."""
    if not settings.OTEL_ENABLED:
        return

    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip("/")

    resource = Resource.create(
        {
            "service.name": settings.service_name,
            "deployment.environment": settings.OTEL_ENVIRONMENT,
            "host.name": settings.host_name,
        }
    )

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    _instrument_clients()


def _instrument_clients() -> None:
    global _clients_instrumentados
    if _clients_instrumentados:
        return

    try:
        HTTPXClientInstrumentor().instrument()
    except Exception:
        logger.debug("HTTPXClientInstrumentor indisponível.")

    _clients_instrumentados = True


def log_telemetry_status() -> None:
    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry desativado via OTEL_ENABLED.")
        return

    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip("/")
    logger.info(
        "OpenTelemetry ativo | service=%s | host=%s | ip=%s | env=%s | endpoint=%s/v1/traces",
        settings.service_name,
        settings.host_name,
        settings.local_ip,
        settings.OTEL_ENVIRONMENT,
        endpoint,
    )


def instrument_fastapi(app: FastAPI) -> None:
    if not settings.OTEL_ENABLED:
        return

    FastAPIInstrumentor.instrument_app(app)


def instrument_sqlalchemy(engine) -> None:
    if not settings.OTEL_ENABLED:
        return

    target = getattr(engine, "sync_engine", engine)
    if id(target) in _engines_instrumentados:
        return

    SQLAlchemyInstrumentor().instrument(engine=target)
    _engines_instrumentados.add(id(target))
