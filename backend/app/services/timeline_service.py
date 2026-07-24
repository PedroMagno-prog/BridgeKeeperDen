from __future__ import annotations

import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.timeline import TimelineEra
from app.db.models.article import Article
from app.db.models.enums import UserRole, VisibilityType
from app.core.fog_of_war import sanitize_article_dict
from app.schemas.timeline import TimelineResponse, TimelineEraResponse, TimelineEventResponse


async def get_timeline(
    db: AsyncSession, world_id: uuid.UUID, role: UserRole
) -> TimelineResponse:
    """Retorna os eventos da linha do tempo e eras agrupadas cronologicamente."""
    # 1. Busca as eras cadastradas
    stmt_eras = (
        select(TimelineEra)
        .where(TimelineEra.world_id == world_id)
        .order_by(TimelineEra.start_sort_order.asc())
    )
    res_eras = await db.execute(stmt_eras)
    eras = list(res_eras.scalars().all())

    # 2. Busca artigos com in_game_sort_order preenchido
    stmt_articles = (
        select(Article)
        .options(selectinload(Article.sections), selectinload(Article.tags))
        .where(
            Article.world_id == world_id,
            Article.in_game_sort_order.isnot(None),
        )
        .order_by(Article.in_game_sort_order.asc())
    )
    res_articles = await db.execute(stmt_articles)
    articles = list(res_articles.scalars().all())

    events: List[TimelineEventResponse] = []
    for art in articles:
        sanitized = sanitize_article_dict(art, role)
        if sanitized is not None:
            snippet = None
            if sanitized.get("sections"):
                first_sec = sanitized["sections"][0]
                snippet = (first_sec.get("content") or "")[:200]

            events.append(
                TimelineEventResponse(
                    article_id=sanitized["id"],
                    title=sanitized["title"],
                    in_game_date=sanitized.get("in_game_date"),
                    in_game_sort_order=sanitized.get("in_game_sort_order"),
                    visibility=sanitized["visibility"],
                    snippet=snippet,
                    is_locked=sanitized.get("is_locked", False),
                )
            )

    return TimelineResponse(
        eras=[TimelineEraResponse.model_validate(e) for e in eras],
        timeline_events=events,
    )
