# Pasta `examples/`

A pasta `examples/` guarda exemplos de uso da estrutura do projeto.
Ela não deve ser considerada parte obrigatória da aplicação em produção.

## Responsabilidade

Use essa pasta para documentar exemplos práticos de:

- integração com APIs externas;
- autenticação OAuth2;
- uso de API key;
- uso de certificado/mTLS;
- payloads de referência;
- chamadas de services;
- padrões de implementação.

## Regras principais

1. Não coloque código essencial de produção apenas aqui.
2. Use exemplos claros e comentados.
3. Não coloque secrets reais.
4. Use valores fictícios em tokens, URLs e credenciais.
5. Mantenha exemplos sincronizados com os arquivos reais do projeto.

## Exemplo de estrutura

```text
examples/
└── oauth2_clients/
    ├── abbiamo_client_example.py
    ├── oauth2_client_credentials_example.py
    └── mtls_client_example.py
```
