"""
Exemplo de API com API Key em header.
"""

from core.oauth2_client import APIAuthConfig, AuthType, OAuth2APIClient


class AbbiamoClient(OAuth2APIClient):
    def __init__(self, api_key: str):
        super().__init__(
            base_url="https://api.abbiamo.io",
            auth_config=APIAuthConfig(
                auth_type=AuthType.API_KEY,
                api_key=api_key,
                api_key_name="x-abbiamo-carrier-key",
                api_key_location="header",
            ),
            timeout=30,
        )

    async def send_confirmed(self, delivery_id: str, event_at: str):
        return await self.request(
            "POST",
            "/v1/delivery/confirmed",
            data={
                "delivery_id": delivery_id,
                "event_at": event_at,
            },
        )
