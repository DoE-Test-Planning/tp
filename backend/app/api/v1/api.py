from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, doe_assets, scenarios

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(doe_assets.router, prefix="/assets", tags=["doe-assets"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"]) 