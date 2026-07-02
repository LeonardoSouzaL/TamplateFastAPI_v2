"""
Exemplo de API OAuth2 com Client Credentials.
"""

from core.oauth2_client import APIAuthConfig, AuthType, OAuth2APIClient


class PartnerOAuthClient(OAuth2APIClient):
    def __init__(
        self,
        *,
        base_url: str,
        token_url: str,
        client_id: str,
        client_secret: str,
    ):
        super().__init__(
            base_url=base_url,
            auth_config=APIAuthConfig(
                auth_type=AuthType.OAUTH2_CLIENT_CREDENTIALS,
                token_url=token_url,
                client_id=client_id,
                client_secret=client_secret,
                scope="orders.read orders.write",
                oauth_client_auth_method="basic",
            ),
            timeout=30,
        )

    async def create_order(self, payload: dict):
        return await self.request(
            "POST",
            "/v1/orders",
            data=payload,
        )
