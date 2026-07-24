import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.auth import get_current_user
from app.db.models.user import User
from app.schemas.world import WorldCreate, WorldResponse, WorldMemberCreate, WorldMemberResponse
from app.services import world_service

router = APIRouter()


@router.get("", response_model=List[WorldResponse])
async def list_worlds(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista os mundos onde o usuário é Mestre ou Jogador."""
    return await world_service.get_user_worlds(db, user)


@router.post("", response_model=WorldResponse, status_code=status.HTTP_201_CREATED)
async def create_world(
    data: WorldCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo mundo. O usuário logado torna-se MESTRE."""
    return await world_service.create_world(db, user, data)


@router.post("/{world_id}/members", response_model=WorldMemberResponse)
async def add_member(
    world_id: uuid.UUID,
    data: WorldMemberCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Adiciona ou atualiza o papel de um membro no mundo."""
    return await world_service.add_world_member(db, world_id, data)
