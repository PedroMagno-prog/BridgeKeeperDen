from fastapi import APIRouter

from app.api.routes import auth, users, worlds

api_router = APIRouter()

api_router.include_router(auth.router,   prefix="/auth",   tags=["Auth"])
api_router.include_router(users.router,  prefix="/users",  tags=["Users"])
api_router.include_router(worlds.router, prefix="/worlds", tags=["Worlds"])
