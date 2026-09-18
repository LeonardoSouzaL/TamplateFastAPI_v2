from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db


async def get_db_psql() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


DbDep = Annotated[AsyncSession, Depends(get_db)]
