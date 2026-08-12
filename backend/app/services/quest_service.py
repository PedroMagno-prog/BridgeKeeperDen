"""Serviço assíncrono para o módulo de Quests e Objetivos."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.enums import UserRole, VisibilityType
from app.db.models.quest import Quest, QuestObjective, QuestCategory, QuestStatus


async def criar_quest(
    db: AsyncSession,
    world_id: uuid.UUID,
    user_id: uuid.UUID,
    role: UserRole,
    *,
    title: str,
    description: str = "",
    category: QuestCategory = QuestCategory.SIDE_QUEST,
    status: QuestStatus = QuestStatus.NOT_STARTED,
    visibility: VisibilityType | None = None,
    rewards: str | None = None,
    article_id: uuid.UUID | None = None,
    objectives: list[dict] | None = None,
) -> Quest:
    """Cria uma nova quest com objetivos em cascata."""
    if visibility is None:
        visibility = VisibilityType.TOTAL if role == UserRole.MESTRE else VisibilityType.NULA

    quest = Quest(
        world_id=world_id,
        created_by=user_id,
        title=title,
        description=description,
        category=category,
        status=status,
        visibility=visibility,
        rewards=rewards,
        article_id=article_id,
    )
    db.add(quest)
    await db.flush()

    if objectives:
        for idx, obj in enumerate(objectives):
            db.add(
                QuestObjective(
                    quest_id=quest.id,
                    description=obj["description"],
                    is_completed=obj.get("is_completed", False),
                    order_index=obj.get("order_index", idx),
                )
            )
        await db.flush()

    return quest


async def listar_quests(
    db: AsyncSession,
    world_id: uuid.UUID,
    role: UserRole,
    *,
    status_filter: QuestStatus | None = None,
    category_filter: QuestCategory | None = None,
    search: str | None = None,
) -> Sequence[Quest]:
    """Lista todas as quests do mundo respeitando a Névoa de Guerra."""
    stmt = (
        select(Quest)
        .options(selectinload(Quest.objectives), selectinload(Quest.article))
        .where(Quest.world_id == world_id)
    )

    if role == UserRole.JOGADOR:
        stmt = stmt.where(Quest.visibility != VisibilityType.NULA)

    if status_filter:
        stmt = stmt.where(Quest.status == status_filter)

    if category_filter:
        stmt = stmt.where(Quest.category == category_filter)

    if search and search.strip():
        stmt = stmt.where(Quest.title.ilike(f"%{search.strip()}%"))

    stmt = stmt.order_by(Quest.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def buscar_quest(
    db: AsyncSession,
    quest_id: uuid.UUID,
    world_id: uuid.UUID,
) -> Quest | None:
    """Busca uma quest específica com objetivos e artigo vinculado."""
    stmt = (
        select(Quest)
        .options(selectinload(Quest.objectives), selectinload(Quest.article))
        .where(Quest.id == quest_id, Quest.world_id == world_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def atualizar_quest(
    db: AsyncSession,
    quest: Quest,
    *,
    title: str | None = None,
    description: str | None = None,
    category: QuestCategory | None = None,
    status: QuestStatus | None = None,
    visibility: VisibilityType | None = None,
    rewards: str | None = None,
    article_id: uuid.UUID | None = None,
    objectives: list[dict] | None = None,
) -> Quest:
    """Atualiza dados de uma quest e substitui seus objetivos se informados."""
    if title is not None:
        quest.title = title
    if description is not None:
        quest.description = description
    if category is not None:
        quest.category = category
    if status is not None:
        quest.status = status
    if visibility is not None:
        quest.visibility = visibility
    if rewards is not None:
        quest.rewards = rewards
    if article_id is not None or "article_id" in locals():
        quest.article_id = article_id

    if objectives is not None:
        await db.execute(delete(QuestObjective).where(QuestObjective.quest_id == quest.id))
        await db.flush()
        for idx, obj in enumerate(objectives):
            db.add(
                QuestObjective(
                    quest_id=quest.id,
                    description=obj["description"],
                    is_completed=obj.get("is_completed", False),
                    order_index=obj.get("order_index", idx),
                )
            )

    await db.flush()
    return quest


async def deletar_quest(
    db: AsyncSession,
    quest: Quest,
) -> None:
    """Remove uma quest (CASCADE deleta os objetivos)."""
    await db.delete(quest)
    await db.flush()


async def toggle_objetivo(
    db: AsyncSession,
    quest_id: uuid.UUID,
    objective_id: uuid.UUID,
) -> QuestObjective | None:
    """Alterna o estado `is_completed` de um objetivo de quest."""
    stmt = select(QuestObjective).where(
        QuestObjective.id == objective_id,
        QuestObjective.quest_id == quest_id,
    )
    result = await db.execute(stmt)
    obj = result.scalar_one_or_none()
    if not obj:
        return None

    obj.is_completed = not obj.is_completed
    await db.flush()
    return obj
