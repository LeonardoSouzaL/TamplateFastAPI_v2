"""
Camada de services da aplicação.

Use esta pasta para centralizar regras de negócio que não devem ficar
nem no endpoint, nem no CRUD.

Fluxo recomendado:
Endpoint -> Service -> CRUD -> Banco
"""

from services.car_service import CarService, car_service
from services.service_order_service import ServiceOrderService, service_order_service
from services.external_status_service import ExternalStatusService

__all__ = [
    "CarService",
    "car_service",
    "ServiceOrderService",
    "service_order_service",
    "ExternalStatusService",
]
