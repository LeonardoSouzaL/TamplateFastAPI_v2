from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    """
    Classe base para services.

    Objetivo:
    - reaproveitar validações comuns;
    - padronizar erros HTTP;
    - evitar repetição de lógica em vários services.
    """

    def not_found(self, detail: str = "Registro não encontrado.") -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

    def bad_request(self, detail: str) -> None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    def conflict(self, detail: str) -> None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )

    async def get_or_404(
        self,
        *,
        db: AsyncSession,
        crud_obj: Any,
        id: int,
        detail: str = "Registro não encontrado.",
    ) -> Any:
        """
        Busca um registro pelo ID usando o CRUD informado.
        Caso não encontre, retorna erro 404.
        """
        obj = await crud_obj.get(db, id=id)

        if not obj:
            self.not_found(detail)

        return obj

    @staticmethod
    def normalize_upper(value: Optional[str]) -> Optional[str]:
        """
        Normaliza strings para uppercase, removendo espaços laterais.
        """
        if value is None:
            return None

        value = value.strip()
        return value.upper() if value else value
