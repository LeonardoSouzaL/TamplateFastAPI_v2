---
name: implementar-otel-loki-fastapi
description: Implementa observabilidade completa em FastAPI com OpenTelemetry, Grafana Tempo, Loki e logs correlacionados por trace_id. Use ao adicionar OTEL/Loki, configurar logging_config, telemetry ou corrigir níveis de log por status HTTP.
---

# Implementar OTEL + Loki (FastAPI)

Antes de alterar arquivos, analise a estrutura e apresente plano curto.

Referência completa: [docs/observability/reference.md](../../docs/observability/reference.md).

Rule de princípios (sempre ativa): `.cursor/rules/333-observability-otel-loki-always.mdc`.

## Checklist de implementação

```text
- [ ] Campos OTEL/LOKI em core/config.py (settings centralizado; .env do servidor alimenta Pydantic em produção)
- [ ] OTEL_DEFER_INIT=True no Swarm + gunicorn_conf.py com post_fork
- [ ] core/host_info.py — IP e sufixo
- [ ] Properties service_name, loki_app_name no Settings
- [ ] core/logging_config.py — LOG_FORMAT, Loki, helpers HTTP
- [ ] core/telemetry.py — setup_base, logging instrumentation, instrumentadores
- [ ] main.py — ordem correta de setup
- [ ] RequestLoggingMiddleware
- [ ] Handler global de exceções
- [ ] ENABLE_TEST_ROUTES para rotas de teste
- [ ] Dependências em requirements.txt
- [ ] instrument_sqlalchemy(engine) se usar SQLAlchemy
```

## Ordem no main.py

```python
def init_observability():
    setup_base_telemetry()
    setup_logging_instrumentation()
    setup_logging()
    log_telemetry_status()

if not settings.OTEL_DEFER_INIT:
    init_observability()
# app + middleware + instrument_fastapi
```

Swarm: `OTEL_DEFER_INIT=True` — `init_observability()` só no `post_fork` de `gunicorn_conf.py`.

## Endpoints

- Traces OTLP: porta **4318** (`OTEL_EXPORTER_OTLP_ENDPOINT` sem `/v1/traces` no config; concatenar em `telemetry.py`)
- Loki: `LOKI_URL` → `/loki/api/v1/push`
- **Nunca** enviar traces para porta 3200

## Gunicorn (Swarm)

Com múltiplos workers, usar `OTEL_DEFER_INIT=True` + `gunicorn_conf.py` (`post_fork` → `init_observability()`). Ver `docs/observability/reference.md` e template `docs/cursor/templates/gunicorn_conf.py`.

## Níveis de log

Centralizar em `core/logging_config.py`:

- `log_for_status_code`, `log_http_exception`, `extract_response_status_code`
- Middleware: 5xx ERROR, 4xx WARNING, resto INFO
- 401/403 sempre ERROR

## LoggingInstrumentor

```python
LoggingInstrumentor().instrument(set_logging_format=True, logging_format=LOG_FORMAT)
```

Evita `KeyError: 'otelTraceID'` com dictConfig próprio.

## Validação

1. App sobe; log `OpenTelemetry ativo | service=...`
2. Requisição com trace_id/span_id reais
3. Tempo: Service Name = `<base>-<env>-<ip>`
4. Loki: filtrar por `{app="..."}`
5. 4xx WARNING, 5xx ERROR

## Anti-padrões

- Duplicar app, dictConfig, instrumentadores
- `os.getenv` fora do config
- `/v1/traces` no `settings` **e** concatenação no `telemetry.py`
- Init OTEL no import do `main.py` com Gunicorn multi-worker sem `post_fork`
- `logger.error` para todo 4xx
- Stack trace ao cliente
- `/teste-erro-loki` em produção

Código de referência: `docs/observability/reference.md`. Em projetos reais: `core/telemetry.py`, `core/logging_config.py`, `core/host_info.py`, `main.py`.
