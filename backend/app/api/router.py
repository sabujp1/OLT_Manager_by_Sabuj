from fastapi import APIRouter
from app.api.endpoints import auth, olts, onus, alarms, dashboard

api_router = APIRouter()

# Register sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(olts.router, prefix="/olts", tags=["olts"])
api_router.include_router(onus.router, prefix="/onus", tags=["onus"])
api_router.include_router(alarms.router, prefix="/alarms", tags=["alarms"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
