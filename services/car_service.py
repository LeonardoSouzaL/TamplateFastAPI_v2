from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_cars import car
from schemas.car_schema import CarCreate, CarUpdate
from models.car_model import Car


class CarService:
    async def list_cars(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Car]:
        """
        Lista carros cadastrados.
        """

        return await car.get_multi(
            db=db,
            skip=skip,
            limit=limit,
        )

    async def get_car_by_id(
        self,
        db: AsyncSession,
        id: int,
    ) -> Car:
        """
        Busca um carro pelo ID.
        """

        db_car = await car.get(
            db=db,
            id=id,
        )

        if not db_car:
            raise HTTPException(
                status_code=404,
                detail="Carro não encontrado.",
            )

        return db_car

    async def create_car(
        self,
        db: AsyncSession,
        payload: CarCreate,
    ) -> Car:
        """
        Cria um novo carro.
        """

        payload.model = payload.model.strip().upper()

        return await car.create(
            db=db,
            obj_in=payload,
        )

    async def update_car(
        self,
        db: AsyncSession,
        id: int,
        payload: CarUpdate,
    ) -> Car:
        """
        Atualiza um carro existente.
        """

        db_car = await self.get_car_by_id(
            db=db,
            id=id,
        )

        if payload.model:
            payload.model = payload.model.strip().upper()

        return await car.update(
            db=db,
            db_obj=db_car,
            obj_in=payload,
        )

    async def delete_car(
        self,
        db: AsyncSession,
        id: int,
    ) -> Car:
        """
        Remove um carro existente.
        """

        await self.get_car_by_id(
            db=db,
            id=id,
        )

        return await car.remove(
            db=db,
            id=id,
        )


car_service = CarService()
