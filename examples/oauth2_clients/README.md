# Pasta `examples/oauth2_clients/`

Esta pasta contém exemplos de consumo de APIs externas usando o client genérico em `core/oauth2_client.py`.

## Exemplos incluídos

```text
oauth2_clients/
├── abbiamo_client_example.py
├── oauth2_client_credentials_example.py
└── mtls_client_example.py
```

## Tipos de autenticação demonstrados

- API Key via header;
- OAuth2 Client Credentials;
- Client ID e Client Secret;
- certificado/mTLS;
- CA bundle customizado;
- headers extras por requisição.

## Exemplo API Key

```python
from core.oauth2_client import APIAuthConfig, AuthType, OAuth2APIClient

client = OAuth2APIClient(
    base_url="https://api.parceiro.com.br",
    auth_config=APIAuthConfig(
        auth_type=AuthType.API_KEY,
        api_key="TOKEN_DE_EXEMPLO",
        api_key_name="x-api-key",
        api_key_location="header",
    ),
)
```

## Exemplo OAuth2 Client Credentials

```python
client = OAuth2APIClient(
    base_url="https://api.parceiro.com.br",
    auth_config=APIAuthConfig(
        auth_type=AuthType.OAUTH2_CLIENT_CREDENTIALS,
        token_url="https://auth.parceiro.com.br/oauth/token",
        client_id="client-id",
        client_secret="client-secret",
        scope="orders.read orders.write",
    ),
)
```

## Regras principais

1. Nunca use credenciais reais nos exemplos.
2. Nunca versione certificados reais.
3. Use `.env` ou variáveis de ambiente em produção.
4. Exemplos devem mostrar a forma de uso, não guardar configuração sensível.
5. Se uma integração virar oficial no sistema, mova a regra para `services/` e deixe aqui apenas um exemplo.
