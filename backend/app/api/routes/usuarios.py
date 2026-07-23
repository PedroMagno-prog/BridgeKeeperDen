"""Rotas de usuário: perfil autenticado."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user
from app.db.models.usuario import Usuario
from app.schemas.usuario import UsuarioOut

router = APIRouter()


@router.get("/me", response_model=UsuarioOut, summary="Retorna o usuário autenticado")
async def me(current_user: Usuario = Depends(get_current_user)):
    return current_user
