"""Serviço assíncrono de World."""
from __future__ import annotations

import uuid

from sqlalchemy import select, func
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
            "invite_code": world.invite_code,
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


async def buscar_mundo_por_codigo_convite(
    db: AsyncSession, invite_code: str
) -> World | None:
    stmt = select(World).where(World.invite_code == invite_code)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def obter_info_convite(
    db: AsyncSession, invite_code: str
) -> dict | None:
    """Retorna informações públicas do mundo para pré-visualização de convite."""
    world = await buscar_mundo_por_codigo_convite(db, invite_code)
    if not world:
        return None

    # Buscar username do criador
    from app.db.models.user import User
    owner_res = await db.execute(select(User.username).where(User.id == world.owner_id))
    owner_username = owner_res.scalar_one_or_none() or "Mestre Desconhecido"

    # Buscar total de membros
    members_res = await db.execute(
        select(func.count(WorldMember.id)).where(WorldMember.world_id == world.id)
    )
    members_count = members_res.scalar_one() or 1

    return {
        "invite_code": world.invite_code,
        "world_id": world.id,
        "world_name": world.name,
        "world_description": world.description,
        "owner_username": owner_username,
        "members_count": members_count,
    }


async def rotacionar_codigo_convite(
    db: AsyncSession, world_id: uuid.UUID
) -> str:
    """Gera um novo código de convite para o mundo."""
    from app.db.models.world import generate_invite_code
    world = await buscar_mundo(db, world_id)
    if not world:
        raise ValueError("Mundo não encontrado")
    world.invite_code = generate_invite_code()
    await db.flush()
    return world.invite_code


async def entrar_no_mundo_por_codigo(
    db: AsyncSession, user_id: uuid.UUID, invite_code: str
) -> tuple[World, WorldMember]:
    """Adiciona o usuário como JOGADOR no mundo via código de convite."""
    world = await buscar_mundo_por_codigo_convite(db, invite_code)
    if not world:
        raise ValueError("INVITE_INVALID")

    membro_existente = await obter_role_no_mundo(db, world.id, user_id)
    if membro_existente:
        raise ValueError("ALREADY_MEMBER")

    novo_membro = WorldMember(
        world_id=world.id,
        user_id=user_id,
        role=UserRole.JOGADOR,
    )
    db.add(novo_membro)
    await db.flush()
    return world, novo_membro


async def listar_membros_do_mundo(
    db: AsyncSession, world_id: uuid.UUID
) -> list[dict]:
    """Lista todos os membros do mundo com detalhes do usuário."""
    from app.db.models.user import User
    stmt = (
        select(WorldMember, User)
        .join(User, User.id == WorldMember.user_id)
        .where(WorldMember.world_id == world_id)
        .order_by(WorldMember.role.asc(), User.username.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "id": member.id,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": member.role,
            "joined_at": getattr(member, 'created_at', None),
        }
        for member, user in rows
    ]


async def remover_membro_do_mundo(
    db: AsyncSession, world_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """Remove um membro do mundo (criador não pode ser removido)."""
    from sqlalchemy import delete
    world = await buscar_mundo(db, world_id)
    if world and world.owner_id == user_id:
        raise ValueError("CANNOT_REMOVE_OWNER")

    stmt = delete(WorldMember).where(
        WorldMember.world_id == world_id,
        WorldMember.user_id == user_id,
    )
    await db.execute(stmt)
    await db.flush()


async def atualizar_role_membro(
    db: AsyncSession, world_id: uuid.UUID, user_id: uuid.UUID, new_role: UserRole
) -> WorldMember | None:
    """Altera a role de um membro no mundo."""
    stmt = select(WorldMember).where(
        WorldMember.world_id == world_id,
        WorldMember.user_id == user_id,
    )
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member:
        return None
    member.role = new_role
    await db.flush()
    return member


async def adicionar_membro_direto(
    db: AsyncSession, world_id: uuid.UUID, user_id_or_email: str, role: UserRole = UserRole.JOGADOR
) -> dict:
    """Adiciona um membro direto ao mundo buscando por username ou e-mail."""
    from app.db.models.user import User
    search_str = user_id_or_email.strip()
    stmt_user = select(User).where(
        (User.email.ilike(search_str)) | (User.username.ilike(search_str))
    )
    res_user = await db.execute(stmt_user)
    target_user = res_user.scalar_one_or_none()
    if not target_user:
        raise ValueError("USER_NOT_FOUND")

    membro_existente = await obter_role_no_mundo(db, world_id, target_user.id)
    if membro_existente:
        raise ValueError("ALREADY_MEMBER")

    novo_membro = WorldMember(
        world_id=world_id,
        user_id=target_user.id,
        role=role,
    )
    db.add(novo_membro)
    await db.flush()

    return {
        "id": novo_membro.id,
        "user_id": target_user.id,
        "username": target_user.username,
        "email": target_user.email,
        "role": novo_membro.role,
        "joined_at": getattr(novo_membro, 'created_at', None),
    }
