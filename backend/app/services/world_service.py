from __future__ import annotations

import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.db.models.user import User
from app.db.models.world import World, WorldMember
from app.db.models.enums import UserRole
from app.schemas.world import WorldCreate, WorldResponse, WorldMemberCreate, WorldMemberResponse


async def create_world(db: AsyncSession, user: User, data: WorldCreate) -> WorldResponse:
    """Cria um novo mundo. O criador torna-se MESTRE automaticamente."""
    world = World(
        name=data.name,
        description=data.description,
        owner_id=user.id,
    )
    db.add(world)
    await db.commit()
    await db.refresh(world)

    response = WorldResponse.model_validate(world)
    response.user_role = UserRole.MESTRE
    return response


async def get_user_worlds(db: AsyncSession, user: User) -> List[WorldResponse]:
    """Lista todos os mundos onde o usuário é Mestre (proprietário/membro) ou Jogador."""
    # Busca mundos criados pelo usuário
    stmt_owned = select(World).where(World.owner_id == user.id)
    res_owned = await db.execute(stmt_owned)
    owned_worlds = list(res_owned.scalars().all())

    # Busca membros de mundos
    stmt_memberships = (
        select(WorldMember)
        .options(selectinload(WorldMember.world))
        .where(WorldMember.user_id == user.id)
    )
    res_memberships = await db.execute(stmt_memberships)
    memberships = list(res_memberships.scalars().all())

    result_map: dict[uuid.UUID, WorldResponse] = {}

    for w in owned_worlds:
        resp = WorldResponse.model_validate(w)
        resp.user_role = UserRole.MESTRE
        result_map[w.id] = resp

    for m in memberships:
        if m.world_id not in result_map:
            resp = WorldResponse.model_validate(m.world)
            resp.user_role = m.role
            result_map[m.world_id] = resp

    return list(result_map.values())


async def add_world_member(
    db: AsyncSession, world_id: uuid.UUID, data: WorldMemberCreate
) -> WorldMemberResponse:
    """Adiciona ou atualiza a associação de um membro em um mundo."""
    stmt = select(WorldMember).where(
        WorldMember.world_id == world_id,
        WorldMember.user_id == data.user_id,
    )
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()

    if member:
        member.role = data.role
    else:
        member = WorldMember(
            world_id=world_id,
            user_id=data.user_id,
            role=data.role,
        )
        db.add(member)

    await db.commit()
    await db.refresh(member)
    return WorldMemberResponse.model_validate(member)
