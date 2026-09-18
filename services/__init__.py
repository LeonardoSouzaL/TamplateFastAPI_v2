"""
Camada de services da aplicação.

Use esta pasta para centralizar regras de negócio que não devem ficar
nem no endpoint, nem no CRUD.

Fluxo recomendado:
Endpoint -> Service -> CRUD -> Banco
"""

from services.lastmile_dashboard_service import (
    LastMileDashboardService,
    lastmile_dashboard_service,
)
from services.lastmile_driver_service import (
    LastMileDriverService,
    lastmile_driver_service,
)

__all__ = [
    "LastMileDashboardService",
    "lastmile_dashboard_service",
    "LastMileDriverService",
    "lastmile_driver_service",
]
