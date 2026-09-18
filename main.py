import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from opentelemetry import trace
from starlette.middleware.cors import CORSMiddleware

from api.api_v1.api import api_router
from core.config import settings
from core.logging_config import RequestLoggingMiddleware, setup_logging
from core.telemetry import (
    instrument_fastapi,
    instrument_sqlalchemy,
    log_telemetry_status,
    setup_base_telemetry,
    setup_logging_instrumentation,
)
from db.session import engine_psql


def init_observability() -> None:
    setup_base_telemetry()
    setup_logging_instrumentation()
    setup_logging()
    log_telemetry_status()


if not settings.OTEL_DEFER_INIT:
    init_observability()

logger = logging.getLogger(settings.service_name)


def api_factory():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        root_path=settings.ROOT_PATH,
        version="0.1.0",
        description=settings.DESCRIPTION,
    )
    app.add_middleware(RequestLoggingMiddleware)

    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app


app = api_factory()

instrument_fastapi(app)
instrument_sqlalchemy(engine_psql)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Erro não tratado na rota %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"},
    )


@app.get(
    f"{app.root_path}/",
    description="Resposta somente para validar se a API subiu. Sem conexão com o banco.",
    summary="Valida se API está no ar",
)
def get_index():
    return {"msg": "API está no ar!"}


@app.get(f"{app.root_path}/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=f"{settings.ROOT_PATH}/openapi.json",
        title="API Docs",
    )


@app.get(f"{app.root_path}/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=f"{settings.ROOT_PATH}/openapi.json",
        title="ReDoc",
    )


@app.get(f"{app.root_path}/openapi.json", include_in_schema=False)
async def get_custom_openapi():
    return get_openapi(
        title=app.title,
        version="0.1.0",
        routes=app.routes,
        description=app.description,
    )


if settings.ENABLE_TEST_ROUTES:

    @app.get(f"{app.root_path}/teste-erro-loki", include_in_schema=False)
    def teste_erro_loki():
        raise Exception("Teste de erro para Loki")

    @app.get(f"{app.root_path}/telemetry-test", include_in_schema=False)
    def telemetry_test():
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("teste-manual-opentelemetry") as span:
            span.set_attribute("app.name", settings.service_name)
            span.set_attribute("test.type", "manual")
        return {
            "status": "ok",
            "message": "Trace manual gerado",
        }


def run():
    uvicorn.run("main:app", reload=True)


if __name__ == "__main__":
    run()
