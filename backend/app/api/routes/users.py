"""Rotas de usuário: perfil autenticado."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.api.deps.database import get_db
from app.db.models.user import User
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut, summary="Retorna o usuário autenticado")
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/search", response_model=list[UserOut], summary="Busca usuários cadastrados por username ou e-mail")
async def search_users(
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Busca usuários por username ou e-mail para convites."""
    if not q.strip():
        return []
    search_str = f"%{q.strip()}%"
    stmt = (
        select(User)
        .where((User.username.ilike(search_str)) | (User.email.ilike(search_str)))
        .limit(10)
    )
    res = await db.execute(stmt)
    return res.scalars().all()
