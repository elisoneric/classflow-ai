from fastapi import APIRouter

from app.presentation.api.routes.auth import router as auth_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)

# Further feature routers are included here as they're built.
