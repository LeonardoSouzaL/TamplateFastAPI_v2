# Pasta `tests/api/`

Esta pasta contém testes voltados para a camada HTTP da aplicação.

## Objetivo

Validar se as rotas respondem corretamente, usando status code, payload de entrada e resposta esperada.

## O que testar

- status code da rota;
- formato da resposta;
- validação de payload;
- query params;
- path params;
- autenticação e autorização, quando existirem;
- comportamento quando o service retorna erro.

## Regras principais

1. Não teste regra de negócio profunda aqui.
2. Mocke o service quando o foco for a rota.
3. Use `httpx.AsyncClient` para rotas async.
4. Valide status code e JSON de resposta.
5. Organize os testes seguindo a mesma versão da API.
