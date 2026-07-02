from typing import Any, List

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api import deps
from schemas.car_schema import CarCreate, CarUpdate, CarInDbBase
from services.car_service import car_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[CarInDbBase])
async def read_cars(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    """
    Lista carros cadastrados.
    """

    logger.info("Consultando carros")

    return await car_service.list_cars(
        db=db,
        skip=skip,
        limit=limit,
    )


@router.get("/{id}", response_model=CarInDbBase)
async def get_car(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
) -> Any:
    """
    Busca um carro pelo ID.
    """

    logger.info("Consultando carro id=%s", id)

    return await car_service.get_car_by_id(
        db=db,
        id=id,
    )


@router.post("/", response_model=CarInDbBase)
async def create_car(
    *,
    db: AsyncSession = Depends(deps.get_db),
    car_in: CarCreate,
) -> Any:
    """
    Cria um novo carro.
    """

    logger.info("Criando carro: %s", car_in.model)

    return await car_service.create_car(
        db=db,
        payload=car_in,
    )


@router.put("/{id}", response_model=CarInDbBase)
async def update_car(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    car_in: CarUpdate,
) -> Any:
    """
    Atualiza um carro existente.
    """

    logger.info("Atualizando carro id=%s", id)

    return await car_service.update_car(
        db=db,
        id=id,
        payload=car_in,
    )


@router.delete("/{id}", response_model=CarInDbBase)
async def delete_car(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
) -> Any:
    """
    Remove um carro pelo ID.
    """

    logger.info("Removendo carro id=%s", id)

    return await car_service.delete_car(
        db=db,
        id=id,
    )
