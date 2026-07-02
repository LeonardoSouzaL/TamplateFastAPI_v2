"""
Cliente HTTP reutilizável para consumo de APIs externas com autenticações comuns.

Suporta:
- Sem autenticação
- API Key em header ou query param
- Bearer token fixo
- Basic Auth
- OAuth2 Client Credentials
- OAuth2 Password Grant
- Certificado/mTLS
- Headers extras por cliente e por requisição

Requer:
    httpx
    fastapi
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Literal, Optional, Tuple

import httpx
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
CertificateType = Optional[str | Tuple[str, str]]


class AuthType(str, Enum):
    """Tipos de autenticação suportados pelo client."""

    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"
    OAUTH2_PASSWORD = "oauth2_password"


class OAuth2Token(BaseModel):
    """Representa o token OAuth2 em cache."""

    access_token: str
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    raw_response: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """
        Considera o token expirado alguns segundos antes do vencimento real
        para evitar erro em chamadas simultâneas ou lentas.
        """

        if not self.expires_at:
            return False

        safety_margin = timedelta(seconds=30)
        return datetime.now(timezone.utc) >= self.expires_at - safety_margin


class APIAuthConfig(BaseModel):
    """Configuração flexível de autenticação para APIs externas."""

    auth_type: AuthType = AuthType.NONE

    # API Key
    api_key: Optional[str] = None
    api_key_name: str = "x-api-key"
    api_key_location: Literal["header", "query"] = "header"

    # Bearer fixo
    bearer_token: Optional[str] = None

    # Basic Auth
    username: Optional[str] = None
    password: Optional[str] = None

    # OAuth2
    token_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    scope: Optional[str] = None
    audience: Optional[str] = None

    # Alguns provedores exigem credenciais no body, outros em Basic Auth
    oauth_client_auth_method: Literal["basic", "body"] = "basic"

    # Password Grant, quando usado por legado/interno
    oauth_username: Optional[str] = None
    oauth_password: Optional[str] = None

    # Campos extras exigidos por provedores específicos
    extra_token_data: Dict[str, Any] = Field(default_factory=dict)
    extra_headers: Dict[str, str] = Field(default_factory=dict)


class ExternalAPIError(HTTPException):
    """Erro padronizado para falhas de comunicação com APIs externas."""

    def __init__(
        self,
        *,
        message: str,
        status_code: int = 502,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        payload: Optional[Any] = None,
        response: Optional[Any] = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={
                "message": message,
                "endpoint": endpoint,
                "method": method,
                "payload_enviado": payload,
                "response": response,
            },
        )


class AbstractOAuth2APIClient(ABC):
    """
    Contrato para clients HTTP com autenticação flexível.

    Use esta classe quando quiser criar clients específicos por parceiro/API,
    mantendo a mesma interface de request.
    """

    @abstractmethod
    async def request(
        self,
        method: HttpMethod,
        endpoint: str,
        *,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def get_access_token(self) -> Optional[str]:
        raise NotImplementedError


class OAuth2APIClient(AbstractOAuth2APIClient):
    """
    Client HTTP genérico para consumo de APIs externas.

    Exemplo:
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

        response = await client.request(
            "POST",
            "/v1/orders",
            data={"order_number": "123"},
        )
    """

    def __init__(
        self,
        *,
        base_url: str,
        auth_config: Optional[APIAuthConfig] = None,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        verify: bool | str = True,
        cert: CertificateType = None,
        follow_redirects: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth_config = auth_config or APIAuthConfig()
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self.verify = verify
        self.cert = cert
        self.follow_redirects = follow_redirects
        self._token: Optional[OAuth2Token] = None

    async def get_access_token(self) -> Optional[str]:
        """
        Retorna token OAuth2 válido quando a configuração exigir OAuth2.
        Para API Key, Bearer fixo, Basic e NONE, retorna None.
        """

        if self.auth_config.auth_type not in {
            AuthType.OAUTH2_CLIENT_CREDENTIALS,
            AuthType.OAUTH2_PASSWORD,
        }:
            return None

        if self._token and not self._token.is_expired:
            return self._token.access_token

        self._token = await self._fetch_oauth2_token()
        return self._token.access_token

    async def request(
        self,
        method: HttpMethod,
        endpoint: str,
        *,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Envia uma requisição HTTP com autenticação aplicada automaticamente.
        """

        method = method.upper()  # type: ignore[assignment]
        url = self._build_url(endpoint)
        request_headers = await self._build_headers(headers=headers)
        request_params = self._build_params(params=params)
        encoded_data = jsonable_encoder(data) if data is not None else None

        try:
            async with httpx.AsyncClient(
                timeout=timeout or self.timeout,
                verify=self.verify,
                cert=self.cert,
                follow_redirects=self.follow_redirects,
            ) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    params=request_params,
                    json=encoded_data if method != "GET" else None,
                )

            await self._log_response(
                method=method,
                url=url,
                payload=encoded_data,
                response=response,
            )

            response.raise_for_status()
            return self._parse_response(response)

        except httpx.HTTPStatusError as exc:
            raise ExternalAPIError(
                message="Erro HTTP ao consumir API externa.",
                status_code=exc.response.status_code,
                endpoint=url,
                method=method,
                payload=encoded_data,
                response=self._safe_response(exc.response),
            ) from exc

        except httpx.RequestError as exc:
            raise ExternalAPIError(
                message="Falha de conexão ao consumir API externa.",
                endpoint=url,
                method=method,
                payload=encoded_data,
                response=str(exc),
            ) from exc

    async def _fetch_oauth2_token(self) -> OAuth2Token:
        if not self.auth_config.token_url:
            raise ValueError("token_url é obrigatório para autenticação OAuth2.")

        data = self._build_token_payload()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            **self.auth_config.extra_headers,
        }
        auth = self._build_token_auth()

        async with httpx.AsyncClient(
            timeout=self.timeout,
            verify=self.verify,
            cert=self.cert,
            follow_redirects=self.follow_redirects,
        ) as client:
            response = await client.post(
                self.auth_config.token_url,
                data=data,
                headers=headers,
                auth=auth,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ExternalAPIError(
                message="Erro ao obter token OAuth2.",
                status_code=exc.response.status_code,
                endpoint=self.auth_config.token_url,
                method="POST",
                payload=self._safe_token_payload(data),
                response=self._safe_response(exc.response),
            ) from exc

        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise ExternalAPIError(
                message="Resposta OAuth2 sem access_token.",
                endpoint=self.auth_config.token_url,
                method="POST",
                payload=self._safe_token_payload(data),
                response=token_data,
            )

        expires_at = self._calculate_expires_at(token_data.get("expires_in"))

        return OAuth2Token(
            access_token=access_token,
            token_type=token_data.get("token_type", "Bearer"),
            expires_at=expires_at,
            refresh_token=token_data.get("refresh_token"),
            raw_response=token_data,
        )

    def _build_token_payload(self) -> Dict[str, Any]:
        auth = self.auth_config

        if auth.auth_type == AuthType.OAUTH2_CLIENT_CREDENTIALS:
            data: Dict[str, Any] = {
                "grant_type": "client_credentials",
            }
        elif auth.auth_type == AuthType.OAUTH2_PASSWORD:
            data = {
                "grant_type": "password",
                "username": auth.oauth_username,
                "password": auth.oauth_password,
            }
        else:
            raise ValueError("Tipo de autenticação OAuth2 inválido para buscar token.")

        if auth.scope:
            data["scope"] = auth.scope

        if auth.audience:
            data["audience"] = auth.audience

        if auth.oauth_client_auth_method == "body":
            data["client_id"] = auth.client_id
            data["client_secret"] = auth.client_secret

        data.update(auth.extra_token_data)
        return {key: value for key, value in data.items() if value is not None}

    def _build_token_auth(self) -> Optional[httpx.BasicAuth]:
        auth = self.auth_config

        if auth.oauth_client_auth_method != "basic":
            return None

        if not auth.client_id or not auth.client_secret:
            return None

        return httpx.BasicAuth(auth.client_id, auth.client_secret)

    async def _build_headers(
        self,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        auth = self.auth_config
        request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            **self.default_headers,
            **auth.extra_headers,
            **(headers or {}),
        }

        if auth.auth_type == AuthType.API_KEY and auth.api_key_location == "header":
            if not auth.api_key:
                raise ValueError("api_key é obrigatória para autenticação API Key.")
            request_headers[auth.api_key_name] = auth.api_key

        elif auth.auth_type == AuthType.BEARER:
            if not auth.bearer_token:
                raise ValueError("bearer_token é obrigatório para autenticação Bearer.")
            request_headers["Authorization"] = f"Bearer {auth.bearer_token}"

        elif auth.auth_type in {AuthType.OAUTH2_CLIENT_CREDENTIALS, AuthType.OAUTH2_PASSWORD}:
            token = await self.get_access_token()
            request_headers["Authorization"] = f"Bearer {token}"

        elif auth.auth_type == AuthType.BASIC:
            # Basic Auth é aplicado pelo método _build_httpx_auth quando necessário.
            pass

        return request_headers

    def _build_params(
        self,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        auth = self.auth_config
        request_params = dict(params or {})

        if auth.auth_type == AuthType.API_KEY and auth.api_key_location == "query":
            if not auth.api_key:
                raise ValueError("api_key é obrigatória para autenticação API Key.")
            request_params[auth.api_key_name] = auth.api_key

        return request_params

    def _build_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint

        endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        return f"{self.base_url}{endpoint}"

    @staticmethod
    def _calculate_expires_at(expires_in: Optional[Any]) -> Optional[datetime]:
        if not expires_in:
            return None

        try:
            seconds = int(expires_in)
        except (TypeError, ValueError):
            return None

        return datetime.now(timezone.utc) + timedelta(seconds=seconds)

    @staticmethod
    def _parse_response(response: httpx.Response) -> Any:
        if response.status_code == 204:
            return None

        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            return response.json()

        return response.text

    @staticmethod
    def _safe_response(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text

    @staticmethod
    def _safe_token_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        protected_keys = {"client_secret", "password"}
        return {
            key: "***" if key in protected_keys else value
            for key, value in payload.items()
        }

    async def _log_response(
        self,
        *,
        method: str,
        url: str,
        payload: Optional[Any],
        response: httpx.Response,
    ) -> None:
        logger.info(
            "external_api_request | method=%s | url=%s | status_code=%s | payload=%s | response=%s",
            method,
            url,
            response.status_code,
            payload,
            response.text,
        )
