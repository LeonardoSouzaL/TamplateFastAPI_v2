---
name: migrar-env-debug-fastapi
description: Migra secrets para .env, cria example-config, .env.example e launch.json para FastAPI com start manual (uvicorn). Use ao configurar ambiente local, perfis homolog/prod ou debug no Cursor/VS Code.
---

# Migrar .env e debug FastAPI

**Invocar** ao migrar ambiente e debug em projetos com **uvicorn** ou **python main.py**.

Complementa `080-security-config-always.mdc`: secrets no `.env`, nunca versionados.

## Arquivos obrigatórios

| Arquivo | Versionar? | Função |
| ------- | ----------- | ------ |
| `.env` | **Não** | Credenciais locais |
| `.env.example` | Sim | Template fictício |
| `core/config.py` | **Não** | Settings real |
| `core/example-config.py` | Sim | Defaults CI; `cp` → config.py |
| `.vscode/launch.json` | Sim | Debug FastAPI + pytest |
| `pytest.ini` | Sim | marker `integration` |

Templates: `docs/cursor/templates/launch.json`, `env-example-header.env`.

## `core/config.py` / `example-config.py`

```python
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

class Settings(BaseSettings):
    SECRET_KEY: str
    DEBUG: bool = False
    API_V1_STR: str = "/api"
    ROOT_PATH: str = "/api-{nome-projeto}"
    PROJECT_NAME: str = "{Nome Projeto}"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
    )

settings = Settings()
```

Regras:

- **Nunca** `if DEBUG:` no corpo da classe para escolher host/credencial.
- **Nunca** credenciais reais em arquivos versionados.
- CI: `cp core/example-config.py core/config.py`

## `.env.example`

1. Cabeçalho `Copy-Item .env.example .env`
2. Valores com `#`, `$`, espaços entre aspas
3. Seção produção (`DEBUG=false`)
4. Bloco homolog comentado no final
5. `INTEGRATION_TEST_*` se houver testes de integração

| Variável | Produção | Homologação |
| -------- | -------- | ----------- |
| `DEBUG` | `false` | `true` |
| `ROOT_PATH` | `/api-{proj}` | `/hg-api-{proj}` |
| `PSQL_HOST` | host prod | host homolog |

## `.vscode/launch.json`

4 configs com `debugpy`, **sem** `--reload`:

1. FastAPI produção — porta 8001, confia no `.env`
2. FastAPI homolog — porta 8000, `env` sobrescreve DEBUG/ROOT_PATH/PSQL_HOST
3. Pytest unitários — `-m "not integration"`
4. Pytest integração — `-m integration` (omitir se não existir)

Placeholders: `{APP_MODULE}`, `{ROOT_PATH_HML}`, `{ROOT_PATH_PROD}`, `{PSQL_HOST_HML}`.

Parar uvicorn do terminal antes de F5.

## README

Documentar: cópia `.env`/`config.py`, tabela de variáveis, comandos homolog vs prod, seção Debug com validação:

```powershell
python -c "from core.config import settings; print(settings.DEBUG, settings.ROOT_PATH, settings.PSQL_HOST)"
```

## Checklist de migração

1. Secrets `config.py` → `.env`
2. `PROJECT_ROOT` + `SettingsConfigDict(env_file=...)` no BaseSettings
3. `.env.example` + `.env` no gitignore
4. `launch.json` adaptado
5. CI copia `example-config.py`
6. Marker `integration` se aplicável
7. README atualizado

## Ao criar/alterar

- Gerar `.env.example`, nunca `.env` real
- Sem `--reload` no debug
- Atualizar **Alterações recentes** no README
