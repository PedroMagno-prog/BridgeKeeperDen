"""Serviço assíncrono de World."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.world import World
from app.db.models.world_member import WorldMember


async def criar_mundo(
    db: AsyncSession, name: str, description: str | None, owner_id: uuid.UUID,
) -> World:
    """
    Cria um novo mundo e automaticamente adiciona o criador como MESTRE.
    """
    world = World(name=name, description=description, owner_id=owner_id)
    db.add(world)
    await db.flush()

    # O criador torna-se automaticamente MESTRE do mundo
    member = WorldMember(
        world_id=world.id, user_id=owner_id, role=UserRole.MESTRE,
    )
    db.add(member)
    await db.flush()

    return world


async def listar_mundos_do_usuario(
    db: AsyncSession, user_id: uuid.UUID,
) -> list[dict]:
    """
    Lista todos os mundos onde o usuário é membro (MESTRE ou JOGADOR).
    Retorna os mundos com o papel do usuário em cada um.
    """
    stmt = (
        select(World, WorldMember.role)
        .join(WorldMember, WorldMember.world_id == World.id)
        .where(WorldMember.user_id == user_id)
        .order_by(World.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    worlds = []
    for world, role in rows:
        worlds.append({
            "id": world.id,
            "name": world.name,
            "description": world.description,
            "owner_id": world.owner_id,
            "created_at": world.created_at,
            "role": role,
        })

    return worlds


async def buscar_mundo(
    db: AsyncSession, world_id: uuid.UUID,
) -> World | None:
    resultado = await db.execute(
        select(World).where(World.id == world_id)
    )
    return resultado.scalar_one_or_none()


async def obter_role_no_mundo(
    db: AsyncSession, world_id: uuid.UUID, user_id: uuid.UUID,
) -> UserRole | None:
    """Retorna o papel do usuário no mundo, ou None se não for membro."""
    resultado = await db.execute(
        select(WorldMember.role).where(
            WorldMember.world_id == world_id,
            WorldMember.user_id == user_id,
        )
    )
    return resultado.scalar_one_or_none()
