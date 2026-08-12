"""Rotas de Mundos (Worlds) — CRUD e gestão de membros."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.api.deps.database import get_db
from app.db.models.enums import UserRole
from app.db.models.user import User
from app.schemas.world import WorldCreate, WorldOut, WorldInviteInfoOut
from app.schemas.world_member import MemberDetailOut, MemberUpdateRoleInput, DirectMemberAddInput
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
        invite_code=world.invite_code,
        owner_id=world.owner_id,
        created_at=world.created_at,
        role=UserRole.MESTRE,
    )


# ── Convites e Aceite ─────────────────────────────────────────────────────────

@router.get("/invite-info/{invite_code}", response_model=WorldInviteInfoOut, summary="Obtém detalhes do convite")
async def obter_info_convite(
    invite_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna detalhes básicos do mundo para o card de confirmação de convite."""
    info = await world_service.obter_info_convite(db, invite_code)
    if not info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código de convite inválido ou expirado.")
    return info


@router.post("/join/{invite_code}", response_model=WorldOut, summary="Aceita convite e entra no mundo")
async def entrar_no_mundo(
    invite_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Adiciona o usuário autenticado ao mundo associado ao código de convite."""
    try:
        world, member = await world_service.entrar_no_mundo_por_codigo(db, current_user.id, invite_code)
        await db.commit()
        return WorldOut(
            id=world.id,
            name=world.name,
            description=world.description,
            invite_code=world.invite_code,
            owner_id=world.owner_id,
            created_at=world.created_at,
            role=member.role,
        )
    except ValueError as e:
        err = str(e)
        if err == "INVITE_INVALID":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código de convite inválido.")
        if err == "ALREADY_MEMBER":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Você já é membro deste mundo.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)


# ── Gestão de Membros ─────────────────────────────────────────────────────────

@router.get("/{world_id}/members", response_model=list[MemberDetailOut], summary="Lista membros do mundo")
async def listar_membros(
    world_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista todos os membros do mundo."""
    role = await world_service.obter_role_no_mundo(db, world_id, current_user.id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado ao mundo.")
    return await world_service.listar_membros_do_mundo(db, world_id)


@router.post("/{world_id}/members", response_model=MemberDetailOut, summary="Adiciona membro direto por email/username")
async def adicionar_membro_direto(
    world_id: uuid.UUID,
    body: DirectMemberAddInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Adiciona um participante buscando por e-mail ou username. Apenas MESTRE."""
    role = await world_service.obter_role_no_mundo(db, world_id, current_user.id)
    if role != UserRole.MESTRE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas MESTRE pode adicionar membros.")
    try:
        res = await world_service.adicionar_membro_direto(db, world_id, body.user_id_or_email, body.role)
        await db.commit()
        return res
    except ValueError as e:
        err = str(e)
        if err == "USER_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
        if err == "ALREADY_MEMBER":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário já é membro deste mundo.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)


@router.put("/{world_id}/members/{target_user_id}/role", response_model=MemberDetailOut, summary="Altera a role de um membro")
async def alterar_role_membro(
    world_id: uuid.UUID,
    target_user_id: uuid.UUID,
    body: MemberUpdateRoleInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Altera o papel (MESTRE / JOGADOR) de um membro. Apenas MESTRE."""
    role = await world_service.obter_role_no_mundo(db, world_id, current_user.id)
    if role != UserRole.MESTRE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas MESTRE pode alterar papéis.")

    updated = await world_service.atualizar_role_membro(db, world_id, target_user_id, body.role)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro não encontrado.")
    await db.commit()

    membros = await world_service.listar_membros_do_mundo(db, world_id)
    target = next((m for m in membros if m["user_id"] == target_user_id), None)
    return target


@router.delete("/{world_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove um membro do mundo")
async def remover_membro(
    world_id: uuid.UUID,
    target_user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove um membro (Mestre remove jogador, ou Jogador remove a si mesmo)."""
    role = await world_service.obter_role_no_mundo(db, world_id, current_user.id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado ao mundo.")

    if role != UserRole.MESTRE and current_user.id != target_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Jogadores só podem remover a si mesmos.")

    try:
        await world_service.remover_membro_do_mundo(db, world_id, target_user_id)
        await db.commit()
    except ValueError as e:
        if str(e) == "CANNOT_REMOVE_OWNER":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O criador do mundo não pode ser removido.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{world_id}/rotate-invite", response_model=dict, summary="Rotaciona o código de convite")
async def rotacionar_convite(
    world_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gera um novo código de convite invalidando o antigo. Apenas MESTRE."""
    role = await world_service.obter_role_no_mundo(db, world_id, current_user.id)
    if role != UserRole.MESTRE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas MESTRE pode rotacionar o código de convite.")

    new_code = await world_service.rotacionar_codigo_convite(db, world_id)
    await db.commit()
    return {"invite_code": new_code}
