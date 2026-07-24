"""Dependência de autenticação via JWT e verificação de papéis no Mundo (Fog of War)."""
from __future__ import annotations

import uuid
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps.database import get_db
from app.core.security import decodificar_token
from app.db.models.user import User
from app.db.models.world import World, WorldMember
from app.db.models.enums import UserRole

bearer_scheme = HTTPBearer(auto_error=True)

_UNAUTH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token inválido ou expirado.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extrai e valida o JWT do header Authorization: Bearer <token>.
    Retorna o objeto User autenticado.
    """
    try:
        payload = decodificar_token(credentials.credentials)
        sub = payload.get("sub")
        if not sub:
            raise _UNAUTH
        user_id = uuid.UUID(sub)
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _UNAUTH

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise _UNAUTH

    return user


async def get_world_role(
    world_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRole:
    """
    Obtém o papel (MESTRE ou JOGADOR) do usuário no mundo especificado.
    Se o usuário for o proprietário (owner_id) do mundo, o papel é MESTRE.
    """
    # 1. Verifica se é o dono do mundo
    stmt_world = select(World).where(World.id == world_id)
    res_world = await db.execute(stmt_world)
    world = res_world.scalar_one_or_none()

    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mundo não encontrado.",
        )

    if world.owner_id == user.id:
        return UserRole.MESTRE

    # 2. Busca o vínculo na tabela world_members
    stmt_member = select(WorldMember).where(
        WorldMember.world_id == world_id,
        WorldMember.user_id == user.id,
    )
    res_member = await db.execute(stmt_member)
    member = res_member.scalar_one_or_none()

    if member:
        return member.role

    # 3. Caso não seja dono nem membro cadastrado
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Você não possui permissão para acessar este mundo.",
    )
