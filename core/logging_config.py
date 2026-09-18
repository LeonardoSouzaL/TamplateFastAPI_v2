"""Configuração de logging reutilizável (stdout + Loki opcional).

Lê tudo de `settings` (core/config.py). O formato correlaciona os logs com
`trace_id`/`span_id`/`service.name` injetados pelo OpenTelemetry.
"""

import importlib.util
import logging
import logging.config
from queue import Queue

from core.config import settings

LOG_FORMAT = (
    "%(asctime)s %(levelname)s "
    "[%(name)s] "
    "[%(filename)s:%(lineno)d] "
    "[trace_id=%(otelTraceID)s "
    "span_id=%(otelSpanID)s "
    "resource.service.name=%(otelServiceName)s] "
    "- %(message)s"
)


class LokiLevelTagFilter(logging.Filter):
    """Adiciona a label ``level`` em cada registro enviado ao Loki.

    O Loki aplica ``retention_stream`` por labels, não pelo texto da mensagem.
    Para manter erros por 7 dias, cada log precisa chegar com
    ``level=error`` ou ``level=critical`` quando aplicável.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        current_tags = getattr(record, "tags", {}) or {}
        record.tags = {
            **current_tags,
            "level": record.levelname.lower(),
        }
        return True


def _loki_disponivel() -> bool:
    return importlib.util.find_spec("logging_loki") is not None


def _loki_tags() -> dict:
    return {
        "app": settings.loki_app_name,
        "host": settings.loki_host_name,
        "env": settings.OTEL_ENVIRONMENT,
    }


def get_logging_config() -> dict:
    log_level = settings.LOG_LEVEL
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": LOG_FORMAT},
        },
        "handlers": {
            "default": {
                "level": log_level,
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
        },
    }


def _attach_loki_handler() -> None:
    """Loki fora do dictConfig: QueueHandler no Python 3.12 exige ``handlers``.

    Falha no Loki não pode quebrar o startup (rule 333).
    """
    if not (settings.LOKI_ENABLED and _loki_disponivel()):
        return

    try:
        import logging_loki
    except Exception:
        return

    log_level = settings.LOG_LEVEL
    try:
        if settings.LOKI_ASYNC:
            handler = logging_loki.LokiQueueHandler(
                Queue(-1),
                url=settings.LOKI_URL,
                tags=_loki_tags(),
                auth=None,
                version="1",
            )
        else:
            handler = logging_loki.LokiHandler(
                url=settings.LOKI_URL,
                tags=_loki_tags(),
                auth=None,
                version="1",
            )
        handler.setLevel(log_level)
        handler.addFilter(LokiLevelTagFilter())
        for logger_name in ("", "uvicorn", "uvicorn.access", "uvicorn.error"):
            logging.getLogger(logger_name).addHandler(handler)
    except Exception:
        logging.getLogger(__name__).warning(
            "Handler Loki indisponível; logs seguem apenas no stdout.",
            exc_info=True,
        )


def setup_logging() -> None:
    logging.config.dictConfig(get_logging_config())
    _attach_loki_handler()


_AUTH_ERROR_CODES = frozenset({401, 403})


def is_auth_error(status_code: int | None) -> bool:
    return status_code in _AUTH_ERROR_CODES


def is_client_error(status_code: int | None) -> bool:
    return status_code is not None and 400 <= status_code < 500


def resolve_log_level(status_code: int | None, *, common_business: bool = False) -> str:
    if status_code is None:
        return "warning" if common_business else "error"
    if status_code >= 500 or is_auth_error(status_code):
        return "error"
    if is_client_error(status_code) or common_business:
        return "warning"
    return "info"


def log_for_status_code(
    logger: logging.Logger,
    status_code: int | None,
    msg: str,
    *args,
    exc_info: bool = False,
    common_business: bool = False,
    **kwargs,
) -> None:
    level = resolve_log_level(status_code, common_business=common_business)
    if level == "info":
        logger.info(msg, *args, **kwargs)
    elif level == "warning":
        logger.warning(msg, *args, **kwargs)
    else:
        logger.error(msg, *args, exc_info=exc_info, **kwargs)


def log_http_exception(
    logger: logging.Logger,
    exc: Exception,
    msg: str,
    *args,
    **kwargs,
) -> None:
    from fastapi import HTTPException

    if isinstance(exc, HTTPException):
        log_for_status_code(logger, exc.status_code, msg, *args, **kwargs)
    else:
        logger.error(msg, *args, **kwargs)


def extract_response_status_code(exc: Exception) -> int | None:
    response = getattr(exc, "response", None)
    if response is not None:
        status_code = getattr(response, "status_code", None)
        if status_code is not None:
            return status_code
    return None


class RequestLoggingMiddleware:
    """Log de acesso HTTP com nível alinhado ao status (rule 333)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        import time

        from opentelemetry import trace

        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        await self.app(scope, receive, send_wrapper)

        duration_ms = (time.perf_counter() - start) * 1000
        method = scope.get("method", "")
        path = scope.get("path", "")

        span = trace.get_current_span()
        ctx = span.get_span_context()
        trace_id = format(ctx.trace_id, "032x") if ctx.trace_id else "0"
        span_id = format(ctx.span_id, "016x") if ctx.span_id else "0"

        access_logger = logging.getLogger(settings.service_name)
        msg = (
            "http.request method=%s path=%s status=%s duration_ms=%.2f "
            "trace_id=%s span_id=%s"
        )
        args = (method, path, status_code, duration_ms, trace_id, span_id)
        level = resolve_log_level(status_code)
        if level == "info":
            access_logger.info(msg, *args)
        elif level == "warning":
            access_logger.warning(msg, *args)
        else:
            access_logger.error(msg, *args)
