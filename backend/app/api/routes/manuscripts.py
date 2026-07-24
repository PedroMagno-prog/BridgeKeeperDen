import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.auth import get_current_user, get_world_role
from app.db.models.user import User
from app.db.models.enums import UserRole
from app.schemas.manuscript import (
    ManuscriptCreate,
    ManuscriptResponse,
    ManuscriptChapterCreate,
    ManuscriptChapterResponse,
)
from app.services import manuscript_service

router = APIRouter()


@router.get("", response_model=List[ManuscriptResponse])
async def list_manuscripts(
    world_id: uuid.UUID,
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Lista os manuscritos/diários de sessão do mundo."""
    return await manuscript_service.list_manuscripts(db, world_id)


@router.post("", response_model=ManuscriptResponse, status_code=status.HTTP_201_CREATED)
async def create_manuscript(
    world_id: uuid.UUID,
    data: ManuscriptCreate,
    user: User = Depends(get_current_user),
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo manuscrito."""
    return await manuscript_service.create_manuscript(db, world_id, user, data)


@router.get("/{manuscript_id}/chapters", response_model=List[ManuscriptChapterResponse])
async def list_chapters(
    world_id: uuid.UUID,
    manuscript_id: uuid.UUID,
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Lista os capítulos de um manuscrito sanitizados pelo Fog of War."""
    return await manuscript_service.get_chapters(db, world_id, manuscript_id, role)


@router.post("/{manuscript_id}/chapters", response_model=ManuscriptChapterResponse, status_code=status.HTTP_201_CREATED)
async def create_chapter(
    world_id: uuid.UUID,
    manuscript_id: uuid.UUID,
    data: ManuscriptChapterCreate,
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo capítulo com formatação e suporte a Fog of War."""
    return await manuscript_service.create_chapter(db, world_id, manuscript_id, role, data)
