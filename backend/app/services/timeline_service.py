"""
Servico assincrono de Timeline.

A timeline NAO possui tabela de eventos propria. Ela compila
automaticamente artigos que possuem in_game_sort_order preenchido
e os agrupa entre as eras cadastradas em timeline_eras.
"""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.article import Article
from app.db.models.enums import UserRole, VisibilityType
from app.db.models.timeline_era import TimelineEra


async def obter_eventos(
    db: AsyncSession,
    world_id: uuid.UUID,
    role: UserRole,
) -> Sequence[Article]:
    """
    Busca artigos com in_game_sort_order preenchido, respeitando Fog of War.
    JOGADOR: filtra NULA no nivel de query (RNF-03).
    """
    stmt = (
        select(Article)
        .where(
            Article.world_id == world_id,
            Article.in_game_sort_order.is_not(None),
        )
        .order_by(Article.in_game_sort_order.asc())
    )

    if role == UserRole.JOGADOR:
        stmt = stmt.where(Article.visibility != VisibilityType.NULA)

    result = await db.execute(stmt)
    return result.scalars().all()


async def listar_eras(
    db: AsyncSession,
    world_id: uuid.UUID,
) -> Sequence[TimelineEra]:
    """Lista todas as eras de um mundo, ordenadas pelo start_sort_order."""
    result = await db.execute(
        select(TimelineEra)
        .where(TimelineEra.world_id == world_id)
        .order_by(TimelineEra.start_sort_order.asc())
    )
    return result.scalars().all()


async def criar_era(
    db: AsyncSession,
    world_id: uuid.UUID,
    *,
    title: str,
    start_sort_order: int,
    end_sort_order: int,
) -> TimelineEra:
    """Cria uma nova era historica."""
    era = TimelineEra(
        world_id=world_id,
        title=title,
        start_sort_order=start_sort_order,
        end_sort_order=end_sort_order,
    )
    db.add(era)
    await db.flush()
    return era


async def deletar_era(
    db: AsyncSession,
    era_id: uuid.UUID,
    world_id: uuid.UUID,
) -> bool:
    """Remove uma era. Retorna True se deletada."""
    result = await db.execute(
        select(TimelineEra).where(
            TimelineEra.id == era_id,
            TimelineEra.world_id == world_id,
        )
    )
    era = result.scalar_one_or_none()
    if not era:
        return False
    await db.delete(era)
    return True
