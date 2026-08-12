"""Rotas do Modulo Quest Journal (Missões) — 6 endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.world_access import WorldContext, get_world_ctx
from app.db.models.enums import UserRole, VisibilityType
from app.db.models.quest import QuestCategory, QuestStatus
from app.schemas.quest import ObjectiveOut, QuestCreate, QuestOut, QuestUpdate
from app.services import quest_service

router = APIRouter()


def sanitize_quest_out(quest: Any, role: UserRole) -> QuestOut | None:
    """Sanitiza dados de uma quest para a resposta API com base na visão."""
    if role == UserRole.MESTRE:
        return QuestOut(
            id=quest.id,
            world_id=quest.world_id,
            title=quest.title,
            description=quest.description,
            category=quest.category,
            status=quest.status,
            visibility=quest.visibility,
            rewards=quest.rewards,
            article_id=quest.article_id,
            article_title=quest.article.title if hasattr(quest, "article") and quest.article else None,
            objectives=[
                ObjectiveOut(
                    id=o.id,
                    description=o.description,
                    is_completed=o.is_completed,
                    order_index=o.order_index,
                )
                for o in quest.objectives
            ],
            created_by=quest.created_by,
            created_at=quest.created_at,
            updated_at=quest.updated_at,
            is_locked=False,
        )

    if quest.visibility == VisibilityType.NULA:
        return None

    if quest.visibility == VisibilityType.PARCIAL:
        return QuestOut(
            id=quest.id,
            world_id=quest.world_id,
            title=quest.title,
            description="Conteúdo protegido por Névoa de Guerra Parcial.",
            category=quest.category,
            status=quest.status,
            visibility=quest.visibility,
            rewards=None,
            article_id=None,
            article_title=None,
            objectives=[],
            created_by=quest.created_by,
            created_at=quest.created_at,
            updated_at=quest.updated_at,
            is_locked=True,
        )

    # TOTAL
    return QuestOut(
        id=quest.id,
        world_id=quest.world_id,
        title=quest.title,
        description=quest.description,
        category=quest.category,
        status=quest.status,
        visibility=quest.visibility,
        rewards=quest.rewards,
        article_id=quest.article_id,
        article_title=quest.article.title if hasattr(quest, "article") and quest.article else None,
        objectives=[
            ObjectiveOut(
                id=o.id,
                description=o.description,
                is_completed=o.is_completed,
                order_index=o.order_index,
            )
            for o in quest.objectives
        ],
        created_by=quest.created_by,
        created_at=quest.created_at,
        updated_at=quest.updated_at,
        is_locked=False,
    )


# ── GET /worlds/{world_id}/quests ─────────────────────────────────────────────

@router.get("/", response_model=list[QuestOut], summary="Lista missões do mundo")
async def listar_quests(
    status: QuestStatus | None = None,
    category: QuestCategory | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Lista missões do mundo com filtros por status, categoria e busca textual."""
    quests = await quest_service.listar_quests(
        db, ctx.world_id, ctx.role, status_filter=status, category_filter=category, search=search,
    )
    result = []
    for q in quests:
        sanitized = sanitize_quest_out(q, ctx.role)
        if sanitized is not None:
            result.append(sanitized)
    return result


# ── POST /worlds/{world_id}/quests ────────────────────────────────────────────

@router.post(
    "/",
    response_model=QuestOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova missão",
)
async def criar_quest(
    body: QuestCreate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Cria uma nova quest com seus objetivos."""
    quest = await quest_service.criar_quest(
        db,
        ctx.world_id,
        ctx.user.id,
        ctx.role,
        title=body.title,
        description=body.description,
        category=body.category,
        status=body.status,
        visibility=body.visibility,
        rewards=body.rewards,
        article_id=body.article_id,
        objectives=[o.model_dump() for o in body.objectives] if body.objectives else [],
    )
    await db.commit()

    loaded = await quest_service.buscar_quest(db, quest.id, ctx.world_id)
    return sanitize_quest_out(loaded, ctx.role)


# ── GET /worlds/{world_id}/quests/{quest_id} ─────────────────────────────────

@router.get("/{quest_id}", response_model=QuestOut, summary="Detalhes de uma missão")
async def buscar_quest(
    quest_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Obtém detalhes da quest com objetivos."""
    quest = await quest_service.buscar_quest(db, quest_id, ctx.world_id)
    if not quest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quest não encontrada.")

    sanitized = sanitize_quest_out(quest, ctx.role)
    if not sanitized:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quest não encontrada.")
    return sanitized


# ── PUT /worlds/{world_id}/quests/{quest_id} ─────────────────────────────────

@router.put("/{quest_id}", response_model=QuestOut, summary="Atualiza uma missão")
async def atualizar_quest(
    quest_id: uuid.UUID,
    body: QuestUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Atualiza dados e objetivos de uma missão. Apenas MESTRE ou criador."""
    quest = await quest_service.buscar_quest(db, quest_id, ctx.world_id)
    if not quest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quest não encontrada.")

    if not ctx.is_mestre and quest.created_by != ctx.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para editar esta quest.")

    update_dict = body.model_dump(exclude_unset=True)
    objs = update_dict.pop("objectives", None)

    await quest_service.atualizar_quest(
        db,
        quest,
        title=update_dict.get("title"),
        description=update_dict.get("description"),
        category=update_dict.get("category"),
        status=update_dict.get("status"),
        visibility=update_dict.get("visibility"),
        rewards=update_dict.get("rewards"),
        article_id=update_dict.get("article_id"),
        objectives=objs,
    )
    await db.commit()

    loaded = await quest_service.buscar_quest(db, quest.id, ctx.world_id)
    return sanitize_quest_out(loaded, ctx.role)


# ── DELETE /worlds/{world_id}/quests/{quest_id} ──────────────────────────────

@router.delete(
    "/{quest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma missão",
)
async def deletar_quest(
    quest_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Remove uma missão. Apenas MESTRE ou criador."""
    quest = await quest_service.buscar_quest(db, quest_id, ctx.world_id)
    if not quest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quest não encontrada.")

    if not ctx.is_mestre and quest.created_by != ctx.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para deletar esta quest.")

    await quest_service.deletar_quest(db, quest)
    await db.commit()


# ── PATCH /worlds/{world_id}/quests/{quest_id}/objectives/{obj_id}/toggle ────

@router.patch(
    "/{quest_id}/objectives/{obj_id}/toggle",
    response_model=ObjectiveOut,
    summary="Alterna conclusão de um objetivo",
)
async def toggle_objetivo(
    quest_id: uuid.UUID,
    obj_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Alterna o checkbox `is_completed` de um objetivo de missão."""
    quest = await quest_service.buscar_quest(db, quest_id, ctx.world_id)
    if not quest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quest não encontrada.")

    if ctx.role == UserRole.JOGADOR and quest.visibility == VisibilityType.NULA:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quest não encontrada.")

    obj = await quest_service.toggle_objetivo(db, quest_id, obj_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")

    await db.commit()
    return ObjectiveOut(
        id=obj.id,
        description=obj.description,
        is_completed=obj.is_completed,
        order_index=obj.order_index,
    )
