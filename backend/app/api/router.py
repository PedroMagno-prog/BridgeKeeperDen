from fastapi import APIRouter

from app.api.routes import auth, usuarios, personagens

api_router = APIRouter()

api_router.include_router(auth.router,        prefix="/auth",        tags=["Auth"])
api_router.include_router(usuarios.router,    prefix="/usuarios",    tags=["Usuários"])
api_router.include_router(personagens.router, prefix="/personagens", tags=["Personagens"])
