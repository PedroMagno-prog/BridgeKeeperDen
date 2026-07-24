"""Rotas de Mundos (Worlds) — CRUD e gestão de membros."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.api.deps.database import get_db
from app.db.models.user import User
from app.schemas.world import WorldCreate, WorldOut
from app.services import world_service

router = APIRouter()


@router.get("/", response_model=list[WorldOut], summary="Lista mundos do usuário")
async def listar_mundos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista todos os mundos onde o usuário é Mestre ou Jogador."""
    mundos = await world_service.listar_mundos_do_usuario(db, current_user.id)
    return mundos


@router.post(
    "/",
    response_model=WorldOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo mundo",
)
async def criar_mundo(
    body: WorldCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria um novo mundo. O usuário logado torna-se automaticamente MESTRE."""
    world = await world_service.criar_mundo(
        db, body.name, body.description, current_user.id,
    )
    await db.commit()
    await db.refresh(world)

    return WorldOut(
        id=world.id,
        name=world.name,
        description=world.description,
        owner_id=world.owner_id,
        created_at=world.created_at,
        role="MESTRE",
    )
