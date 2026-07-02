"""
Arquivo opcional para manter compatibilidade com o padrão atual do template.

Se você já possui um core/request.py, pode substituir ou apenas importar
OAuth2APIClient nele, mantendo RequestClient antigo durante a transição.
"""

from core.oauth2_client import (
    APIAuthConfig,
    AuthType,
    ExternalAPIError,
    OAuth2APIClient,
    OAuth2Token,
)

__all__ = [
    "APIAuthConfig",
    "AuthType",
    "ExternalAPIError",
    "OAuth2APIClient",
    "OAuth2Token",
]
