# Pasta `tests/services/`

Esta pasta contém testes unitários da camada `services/`.

## Objetivo

Testar regras de negócio sem depender diretamente dos endpoints HTTP.

## O que testar

- normalização de dados;
- validação de duplicidade;
- erros 400, 404 e 409;
- transição de status;
- bloqueios de fluxo;
- chamada correta ao CRUD;
- payloads montados para integração.

## Exemplo

```python
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from services.car_service import car_service


@pytest.mark.asyncio
async def test_get_car_by_id_deve_retornar_404_quando_nao_existir():
    db = AsyncMock()

    with patch("services.car_service.crud_car.get", new=AsyncMock(return_value=None)):
        with pytest.raises(HTTPException) as exc:
            await car_service.get_car_by_id(db=db, id=999)

    assert exc.value.status_code == 404
```

## Regras principais

1. Use `AsyncMock` para métodos assíncronos.
2. Não teste detalhes internos do CRUD aqui.
3. Teste o comportamento esperado do service.
4. Para erro, valide `status_code` e `detail`.
5. Para sucesso, valide se o retorno e a chamada ao CRUD estão corretos.
