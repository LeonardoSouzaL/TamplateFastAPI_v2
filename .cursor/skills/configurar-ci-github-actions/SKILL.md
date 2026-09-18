---
name: configurar-ci-github-actions
description: Configura pipeline GitHub Actions para pytest unitário em projetos FastAPI template, com UTF-8 em requirements e example-config. Use ao criar ou alterar CI, workflows .yml ou corrigir falha de encoding no Linux.
---

# Configurar CI GitHub Actions

Complementa `070-tests-auto.mdc` e `080-security-config-always.mdc`.

CI roda **apenas** testes unitários (`-m "not integration"`). Integração fica fora do pipeline.

## Arquivos

| Arquivo | Função |
| ------- | ------ |
| `.github/workflows/ci.yml` | Pipeline |
| `requirements.txt` | UTF-8 obrigatório |
| `requirements-dev.txt` | UTF-8 obrigatório |
| `pytest.ini` | marker `integration` |
| `core/example-config.py` | Copiada no CI |

Template: `docs/cursor/templates/ci.yml`.

## UTF-8 em requirements

UTF-16 quebra `pip install` no Linux.

Verificar:

```powershell
python -c "b=open('requirements.txt','rb').read(2); print('UTF-16!' if b in (b'\xff\xfe', b'\xfe\xff') else 'OK')"
```

Corrigir:

```powershell
python -c "p='requirements.txt'; open(p,'w',encoding='utf-8',newline='\n').write(open(p,encoding='utf-16').read())"
```

## Step de verificação no workflow

```yaml
- name: Verify requirements files are UTF-8
  run: |
    python -c "
    import pathlib
    for name in ('requirements.txt', 'requirements-dev.txt'):
        p = pathlib.Path(name)
        if not p.exists():
            continue
        raw = p.read_bytes()
        if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
            raise SystemExit(f'{name} must be UTF-8, not UTF-16')
        raw.decode('utf-8')
    print('requirements encoding OK')
    "
```

## Pipeline — regras

- Secrets fictícios em `env:` do workflow
- `cp core/example-config.py core/config.py` se config não versionado
- `pytest tests/ -m "not integration" -v --tb=short`
- `unixodbc-dev` no Ubuntu se usar pyodbc
- Python alinhado ao projeto (ex. 3.11)
- Branches: main, master, develop

## `pytest.ini`

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
markers =
    integration: testes contra banco/rede real (fora do CI)
```

## Ao criar/alterar CI

1. UTF-8 em requirements
2. Step de encoding
3. Copiar example-config
4. Só unitários no CI
5. README (seção CI) + **Alterações recentes**

Workflow completo: ver `docs/cursor/templates/ci.yml`.
