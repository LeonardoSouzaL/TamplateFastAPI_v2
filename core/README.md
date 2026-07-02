# Pasta `core/`

A pasta `core/` concentra recursos compartilhados e utilitários estruturais da aplicação.
Ela deve conter código reutilizável que pode ser usado por endpoints, services, CRUDs ou integrações.

## Exemplos de arquivos

```text
core/
├── config.py
├── example-config.py
├── filters.py
├── request.py
├── oauth2_client.py
└── xml_render.py
```

## Responsabilidade

Use `core/` para:

- configurações globais;
- leitura de variáveis de ambiente;
- clientes HTTP reutilizáveis;
- autenticação com APIs externas;
- filtros genéricos;
- renderização de XML;
- helpers técnicos compartilhados.

## Quando usar `core` e quando usar `services`

Use `core` para recursos genéricos e reutilizáveis.
Use `services` para regra de negócio de um domínio específico.

Exemplo:

```text
core/oauth2_client.py       -> cliente genérico para qualquer API OAuth2
services/order_service.py   -> regra de negócio de ordem de serviço
```

## Regras principais

1. Não coloque regra de endpoint aqui.
2. Não coloque lógica específica demais de um domínio se ela pertencer a `services`.
3. Centralize clients externos em `core/request.py` ou `core/oauth2_client.py`.
4. Não exponha secrets fixos no código.
5. Use `core/config.py` para carregar variáveis via `.env`.

## Exemplo de uso do client OAuth2/API externa

```python
from core.oauth2_client import APIAuthConfig, AuthType, OAuth2APIClient

client = OAuth2APIClient(
    base_url="https://api.parceiro.com.br",
    auth_config=APIAuthConfig(
        auth_type=AuthType.API_KEY,
        api_key="TOKEN",
        api_key_name="x-api-key",
    ),
)

response = await client.request(
    method="GET",
    endpoint="/v1/status",
)
```
