"""
Exemplo de API com OAuth2 + certificado mTLS.

cert pode ser:
- caminho único para arquivo .pem contendo certificado + chave
- tupla: (caminho_certificado, caminho_chave_privada)
"""

from core.oauth2_client import APIAuthConfig, AuthType, OAuth2APIClient


class MTLSPartnerClient(OAuth2APIClient):
    def __init__(
        self,
        *,
        base_url: str,
        token_url: str,
        client_id: str,
        client_secret: str,
        cert_path: str,
        key_path: str,
        ca_bundle_path: str | bool = True,
    ):
        super().__init__(
            base_url=base_url,
            auth_config=APIAuthConfig(
                auth_type=AuthType.OAUTH2_CLIENT_CREDENTIALS,
                token_url=token_url,
                client_id=client_id,
                client_secret=client_secret,
                oauth_client_auth_method="basic",
            ),
            cert=(cert_path, key_path),
            verify=ca_bundle_path,
            timeout=60,
        )

    async def send_event(self, payload: dict):
        return await self.request(
            "POST",
            "/v1/events",
            data=payload,
        )
