from typing import Any, Dict, Optional

from fastapi.encoders import jsonable_encoder

from core.request import APIClient
from services.base_service import BaseService


class ExternalStatusService(BaseService):
    """
    Exemplo de service para integração externa.

    Este arquivo mostra como consumir uma API externa sem colocar httpx
    diretamente no endpoint.

    Uso esperado:
        service = ExternalStatusService(
            base_url="https://api.externa.com.br",
            apikey="TOKEN",
            api_key_header_name="x-api-key",
        )
        response = await service.send_status(...)
    """

    def __init__(
        self,
        *,
        base_url: str,
        apikey: Optional[str] = None,
        api_key_header_name: str = "x-api-key",
        timeout: int = 30,
    ) -> None:
        self.client = APIClient(
            base_url=base_url,
            apikey=apikey,
            api_key_header_name=api_key_header_name,
            timeout=timeout,
        )

    async def send_status(
        self,
        *,
        endpoint: str,
        order_number: str,
        status_value: str,
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Envia status para uma API parceira.
        """
        if not order_number:
            self.bad_request("O número da ordem é obrigatório para enviar status.")

        if not status_value:
            self.bad_request("O status é obrigatório para enviar status.")

        payload = {
            "order_number": order_number,
            "status": status_value,
        }

        if extra_payload:
            payload.update(extra_payload)

        return await self.client.request(
            method="POST",
            endpoint=endpoint,
            data=jsonable_encoder(payload),
        )
