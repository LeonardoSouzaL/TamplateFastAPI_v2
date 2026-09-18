---
name: deploy-swarm-fastapi
description: Adapta FastAPI para produção no Docker Swarm — Dockerfile, stack.yml, workflow GHCR, healthcheck e OTEL no Swarm. Use ao configurar deploy Swarm, criar deploy-swarm.yml ou corrigir rolling update com mode host.
---

# Deploy Docker Swarm (FastAPI)

**Invocar** com `@deploy-swarm-fastapi` ou `@130-fastapi-swarm-deploy-manual`.

Contexto completo: [docs/contexto_infra_swarm_cursor.md](../../docs/contexto_infra_swarm_cursor.md).

Rules de princípio: `130-fastapi-swarm-deploy-manual.mdc`, `131-docker-swarm-stack-auto.mdc`, `132-github-actions-swarm-deploy-auto.mdc`.

## Gate obrigatório — perguntar antes de gerar

| Pergunta | Exemplo | Uso |
| -------- | ------- | --- |
| `APP_PORT` | `8020` | Dockerfile, stack, healthcheck, HAProxy |
| `STACK_NAME` | `minha_api` | Workflow, `docker stack deploy` (**fixo!**) |
| Módulo ASGI | `main:app` | Dockerfile CMD, stack `command` |
| Hostname curto | `minha-api` | `hostname: "minha-api-{{.Node.Hostname}}"` |
| Domínio / CORS | URL produção | `ALLOWED_ORIGINS` |
| Alembic | sim/não | Step opcional no workflow |

Nunca assumir `8000`/`8010` — cluster com várias apps em `mode: host`.

## Infra resumida

```text
GitHub push main
  → CI (ci.yml, ubuntu-latest, pytest)
      ├─ falhou → Deploy NÃO roda
      └─ sucesso → Deploy Swarm (deploy-swarm.yml, self-hosted, python-app-01)
             → Build + push GHCR → docker stack deploy
             → Swarm (192.168.0.223/224/225) → HAProxy → usuários
```

**1 push na main = 1 run de CI + 0 ou 1 run de Deploy** (o deploy só existe se o CI ficar verde).

- Rede overlay: `app_network` (externa)
- Portas: `mode: host`; réplicas `3`, `max_replicas_per_node: 1`
- Rolling update: **`stop-first`** (obrigatório com host port)
- `.env` real: `/opt/envs/{app}.env` (`chmod 600`) — nunca no Git

## Checklist de artefatos

| Artefato | Template |
| -------- | -------- |
| `Dockerfile` | `docs/cursor/templates/Dockerfile.fastapi` |
| `.dockerignore` | `docs/cursor/templates/dockerignore` |
| `deploy/stack.yml` | `docs/cursor/templates/deploy/stack.yml` |
| `deploy/scripts/force-image-rollout.sh` | `docs/cursor/templates/deploy/scripts/force-image-rollout.sh` |
| `.github/workflows/deploy-swarm.yml` | `docs/cursor/templates/deploy-swarm.yml` |
| `.env.example` | `docs/cursor/templates/env-example-swarm.env` |
| `gunicorn_conf.py` | `docs/cursor/templates/gunicorn_conf.py` |
| `GET /health` | `{"status": "ok"}` em `main.py` |

## Dockerfile — pontos críticos

- `ARG CACHE_BUST` + `RUN test -n "${CACHE_BUST}"` **antes** de `COPY . .`
- Instalar `curl` (healthcheck)
- `gunicorn` + `uvicorn.workers.UvicornWorker` + **`-c gunicorn_conf.py`** (OTEL no `post_fork`)
- `command` na stack **sobrescreve** CMD da imagem

## `deploy/stack.yml` — pontos críticos

| Item | Regra |
| ---- | ----- |
| `ports` | `mode: host` |
| `update_config.order` | **`stop-first`** |
| `healthcheck` | `curl -f http://localhost:$${APP_PORT}/health` |
| OTEL | `OTEL_APPEND_IP_SUFFIX=False`, `OTEL_DEFER_INIT=True` no `.env` do servidor |

## Gunicorn e OpenTelemetry

`BatchSpanProcessor` não é fork-safe. Com `--workers 4`:

1. Copiar `docs/cursor/templates/gunicorn_conf.py` para a raiz do projeto.
2. Expor `init_observability()` em `main.py` (ver `docs/observability/reference.md`).
3. `OTEL_DEFER_INIT=True` no `.env` do servidor.
4. Gunicorn com `-c gunicorn_conf.py` no Dockerfile e na stack.

Sem isso, traces podem falhar silenciosamente ou travar o export após fork.

## Gate — deploy só após CI verde (não paralelo)

O deploy é um **pipeline separado** do `ci.yml` (rule `075`), mas **encadeado** — não roda em paralelo. "Pipeline separado" significa **workflow distinto** (CI testa em `ubuntu-latest`; deploy publica no `self-hosted`), **não** "rodar ao mesmo tempo".

```text
push main → CI (pytest) → success → Deploy Swarm (GHCR + stack deploy)
                        → failure → deploy NÃO roda
```

Gatilho **obrigatório** do `deploy-swarm.yml` quando existe `ci.yml` na main:

```yaml
on:
  workflow_run:
    workflows: ["CI"]   # nome EXATO do workflow em ci.yml (name: CI)
    types:
      - completed
    branches:
      - main

jobs:
  deploy:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: [self-hosted, linux, swarm]
```

- **Proibido** `on: push` no deploy quando o projeto já tem `ci.yml` na main (causa deploy paralelo ao CI, permitindo publicar código que não passou nos testes).
- **PRs:** só o CI roda; o deploy **não** — o filtro `branches: [main]` do `workflow_run` restringe o deploy a eventos concluídos na main.
- **Se o projeto NÃO tiver CI (`ci.yml`):** perguntar ao usuário antes de usar `on: push` no deploy. Preferir criar o CI primeiro (Skill `configurar-ci-github-actions`) e encadear via `workflow_run`.

## SHA do commit — armadilha do `workflow_run`

Em `workflow_run`, `github.sha` **não** é o commit testado pelo CI. Usar sempre:

```yaml
${{ github.event.workflow_run.head_sha }}
```

Sugestão: definir uma variável de ambiente única no workflow e reutilizar:

```yaml
env:
  COMMIT_SHA: ${{ github.event.workflow_run.head_sha }}
```

Aplicar `head_sha` (`COMMIT_SHA`) em:

- `actions/checkout@v4` → `ref: ${{ env.COMMIT_SHA }}`;
- tag da imagem GHCR → `ghcr.io/...:${{ env.COMMIT_SHA }}`;
- `CACHE_BUST` no build;
- validação do step **Wait for replicas** (grep da tag SHA nas réplicas).

## Workflow `deploy-swarm.yml`

```yaml
runs-on: [self-hosted, linux, swarm]
```

Fluxo: gate (`workflow_run.conclusion == 'success'`) → checkout `ref: COMMIT_SHA` → build/push GHCR (`CACHE_BUST=COMMIT_SHA`) → `docker pull` → validar cluster + `.env` → Alembic opcional → `stack deploy --with-registry-auth` → wait 600s (`3/3` mesma tag `COMMIT_SHA`).

Variáveis adaptar por projeto:

```yaml
env:
  STACK_NAME: minha_app
  STACK_FILE: deploy/stack.yml
  ENV_FILE: /opt/envs/minha-app.env
  SERVICE_NAME: minha_app_web
  COMMIT_SHA: ${{ github.event.workflow_run.head_sha }}
```

Referência real implementada: `api-crm` (`.github/workflows/deploy-swarm.yml` e `docs/infra/deploy-swarm-api-crm.md`, seção Deploy).

## Observabilidade no Swarm

```env
OTEL_SERVICE_NAME=NomeAplicacaoFastAPI
LOKI_APP_NAME=NomeAplicacaoFastAPI
OTEL_ENVIRONMENT=production
OTEL_APPEND_IP_SUFFIX=False
OTEL_DEFER_INIT=True
```

Repassar no `environment` da stack: `OTEL_ENABLED`, `OTEL_SERVICE_NAME`, `OTEL_APPEND_ENV`, `OTEL_APPEND_IP_SUFFIX`, `OTEL_DEFER_INIT`, `OTEL_ENVIRONMENT`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `LOKI_ENABLED`, `LOKI_URL`, `LOKI_APP_NAME`, `LOG_LEVEL`. Nome no Tempo/Loki: `<base>-<ambiente>` (sem octeto IP).

## HAProxy (exemplo)

```haproxy
backend minha_app_fastapi
    balance roundrobin
    option httpchk GET /health
    server python-app-01 192.168.0.223:${APP_PORT} check
    server python-app-02 192.168.0.224:${APP_PORT} check
    server python-app-03 192.168.0.225:${APP_PORT} check
```

Não fazer strip de path no HAProxy se o projeto usa `ROOT_PATH`.

## Erros comuns

| Sintoma | Solução |
| ------- | ------- |
| `host-mode port already in use` | `stop-first`; `force-image-rollout.sh` |
| Réplicas com tags diferentes | `bash deploy/scripts/force-image-rollout.sh <STACK> <image:sha>` |
| Código antigo na imagem | Verificar `CACHE_BUST` no build |
| `Invalid requirement` no build | `requirements.txt` UTF-8 (Skill `configurar-ci-github-actions`) |
| Healthcheck falha | Criar `GET /health`; validar `APP_PORT` |
| Traces ausentes no Tempo com Gunicorn | `OTEL_DEFER_INIT=True` + `gunicorn_conf.py` + `-c gunicorn_conf.py` |

## Validação no manager

```bash
docker service ls | grep <STACK_NAME>
docker service ps <STACK_NAME>_web --filter "desired-state=running" --format '{{.Node}} {{.Image}}'
curl -fsS http://192.168.0.223:<APP_PORT>/health
```

Esperado: **3 linhas**, **uma única tag** SHA.

## Proibido

- Gerar arquivos sem perguntar `APP_PORT` / `STACK_NAME`.
- `start-first` com `mode: host`.
- Versionar `.env` real ou secrets.
- `ENABLE_TEST_ROUTES` em produção.
- Banco/Redis/uploads dentro do container.
- Misturar deploy dentro de `ci.yml` (manter workflows separados).
- `on: push` no `deploy-swarm.yml` quando existe `ci.yml` na main (usar `workflow_run` + gate de sucesso).
- Usar `github.sha` em vez de `github.event.workflow_run.head_sha` no deploy via `workflow_run`.

## Ao concluir

1. Listar arquivos criados/alterados e valores escolhidos.
2. Lembrar criação de `/opt/envs/{app}.env` no servidor.
3. README + **Alterações recentes**.
