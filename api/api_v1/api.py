from fastapi import APIRouter

from api.api_v1.endpoints import (
    lastmile_dashboard,
    lastmile_os_client,
    lastmile_os_driver,
    lastmile_os_overview,
    lastmile_os_pa,
    lastmile_os_status,
)

api_router = APIRouter()
api_router.include_router(
    lastmile_dashboard.router,
    prefix="/lastmile",
    tags=["lastmile-dashboard"],
)
api_router.include_router(
    lastmile_os_status.router,
    prefix="/lastmile",
    tags=["lastmile-os-status"],
)
api_router.include_router(
    lastmile_os_pa.router,
    prefix="/lastmile",
    tags=["lastmile-os-pa"],
)
api_router.include_router(
    lastmile_os_client.router,
    prefix="/lastmile",
    tags=["lastmile-os-client"],
)
api_router.include_router(
    lastmile_os_driver.router,
    prefix="/lastmile",
    tags=["lastmile-os-driver"],
)
api_router.include_router(
    lastmile_os_overview.router,
    prefix="/lastmile",
    tags=["lastmile-os-overview"],
)
