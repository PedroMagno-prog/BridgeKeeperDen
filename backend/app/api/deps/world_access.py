"""
Dependency de acesso ao mundo.

Valida que o world_id existe e que o usuario logado e membro,
retornando a role do usuario no mundo.
"""
from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.api.deps.database import get_db
from app.db.models.enums import UserRole
from app.db.models.user import User
from app.services import world_service


class WorldContext:
    """Contexto de acesso ao mundo: usuario + role + world_id."""

    def __init__(self, user: User, role: UserRole, world_id: uuid.UUID):
        self.user = user
        self.role = role
        self.world_id = world_id

    @property
    def is_mestre(self) -> bool:
        return self.role == UserRole.MESTRE


async def get_world_ctx(
    world_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorldContext:
    """
    FastAPI dependency que valida acesso ao mundo.

    - Verifica se o mundo existe (404 se nao).
    - Verifica se o usuario e membro (403 se nao).
    - Retorna WorldContext com user, role e world_id.
    """
    world = await world_service.buscar_mundo(db, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mundo nao encontrado.",
        )

    role = await world_service.obter_role_no_mundo(db, world_id, current_user.id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao e membro deste mundo.",
        )

    return WorldContext(user=current_user, role=role, world_id=world_id)
