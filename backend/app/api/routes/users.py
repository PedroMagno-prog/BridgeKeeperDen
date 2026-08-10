"""Rotas de usuário: perfil autenticado."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user
from app.db.models.user import User
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut, summary="Retorna o usuário autenticado")
async def me(current_user: User = Depends(get_current_user)):
    return current_user
