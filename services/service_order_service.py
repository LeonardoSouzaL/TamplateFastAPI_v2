from typing import Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_service_orders import crud_service_order
from schemas.service_order_schema import ServiceOrderCreate, ServiceOrderUpdate
from services.base_service import BaseService


class ServiceOrderService(BaseService):
    """
    Service responsável pelas regras de negócio de ordens de serviço.

    Exemplo de responsabilidades:
    - impedir OS duplicada;
    - controlar transição de status;
    - centralizar filtros de busca;
    - evitar regra de negócio pesada no endpoint.
    """

    async def create_order(
        self,
        *,
        db: AsyncSession,
        payload: ServiceOrderCreate,
    ) -> Any:
        """
        Cria uma ordem de serviço, impedindo duplicidade por order_number.
        """
        order_number = self.normalize_upper(payload.order_number)

        existing_order = await crud_service_order.get_last_by_filters(
            db,
            filters={
                "order_number": {"operator": "==", "value": order_number}
            },
        )

        if existing_order:
            self.conflict("Já existe uma ordem de serviço cadastrada com este número.")

        payload_data = payload.model_dump()
        payload_data["order_number"] = order_number

        normalized_payload = ServiceOrderCreate(**payload_data)
        return await crud_service_order.create(db, obj_in=normalized_payload)

    async def update_order(
        self,
        *,
        db: AsyncSession,
        id: int,
        payload: ServiceOrderUpdate,
    ) -> Any:
        """
        Atualiza uma ordem de serviço existente.
        """
        db_order = await self.get_or_404(
            db=db,
            crud_obj=crud_service_order,
            id=id,
            detail="Ordem de serviço não encontrada.",
        )

        return await crud_service_order.update(db, db_obj=db_order, obj_in=payload)

    async def cancel_order(
        self,
        *,
        db: AsyncSession,
        id: int,
    ) -> Any:
        """
        Cancela uma OS, respeitando regras simples de transição de status.
        """
        db_order = await self.get_or_404(
            db=db,
            crud_obj=crud_service_order,
            id=id,
            detail="Ordem de serviço não encontrada.",
        )

        if db_order.status == "FINALIZADA":
            self.bad_request("Não é possível cancelar uma ordem já finalizada.")

        if db_order.status == "CANCELADA":
            self.bad_request("Esta ordem já está cancelada.")

        payload = ServiceOrderUpdate(status="CANCELADA")
        return await crud_service_order.update(db, db_obj=db_order, obj_in=payload)

    async def finish_order(
        self,
        *,
        db: AsyncSession,
        id: int,
    ) -> Any:
        """
        Finaliza uma OS, impedindo finalizar OS cancelada.
        """
        db_order = await self.get_or_404(
            db=db,
            crud_obj=crud_service_order,
            id=id,
            detail="Ordem de serviço não encontrada.",
        )

        if db_order.status == "CANCELADA":
            self.bad_request("Não é possível finalizar uma ordem cancelada.")

        if db_order.status == "FINALIZADA":
            self.bad_request("Esta ordem já está finalizada.")

        payload = ServiceOrderUpdate(status="FINALIZADA")
        return await crud_service_order.update(db, db_obj=db_order, obj_in=payload)

    async def list_orders(
        self,
        *,
        db: AsyncSession,
        status: Optional[str] = None,
        order_number: Optional[str] = None,
        external_order_number: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Any]:
        """
        Lista ordens com filtros opcionais.
        """
        filters = []

        if status:
            filters.append({
                "field": "status",
                "operator": "==",
                "value": self.normalize_upper(status),
            })

        if order_number:
            filters.append({
                "field": "order_number",
                "operator": "ilike",
                "value": self.normalize_upper(order_number),
            })

        if external_order_number:
            filters.append({
                "field": "external_order_number",
                "operator": "ilike",
                "value": self.normalize_upper(external_order_number),
            })

        return await crud_service_order.get_multi_filters(
            db,
            filters=filters,
            order_by="id",
            order_desc=True,
            limit=limit,
            offset=offset,
        )


service_order_service = ServiceOrderService()
