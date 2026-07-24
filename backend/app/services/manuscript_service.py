from __future__ import annotations

import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.db.models.user import User
from app.db.models.manuscript import Manuscript, ManuscriptChapter
from app.db.models.enums import UserRole, VisibilityType
from app.core.fog_of_war import sanitize_chapter_dict
from app.schemas.manuscript import (
    ManuscriptCreate,
    ManuscriptResponse,
    ManuscriptChapterCreate,
    ManuscriptChapterResponse,
)


async def list_manuscripts(db: AsyncSession, world_id: uuid.UUID) -> List[ManuscriptResponse]:
    """Lista os manuscritos cadastrados no mundo."""
    stmt = (
        select(Manuscript)
        .options(selectinload(Manuscript.chapters))
        .where(Manuscript.world_id == world_id)
        .order_by(Manuscript.created_at.desc())
    )
    res = await db.execute(stmt)
    manuscripts = list(res.scalars().all())
    return [ManuscriptResponse.model_validate(m) for m in manuscripts]


async def create_manuscript(
    db: AsyncSession, world_id: uuid.UUID, user: User, data: ManuscriptCreate
) -> ManuscriptResponse:
    """Cria um novo manuscrito."""
    ms = Manuscript(
        world_id=world_id,
        title=data.title,
        created_by=user.id,
    )
    db.add(ms)
    await db.commit()
    await db.refresh(ms)

    stmt = select(Manuscript).options(selectinload(Manuscript.chapters)).where(Manuscript.id == ms.id)
    res = await db.execute(stmt)
    loaded = res.scalar_one()
    return ManuscriptResponse.model_validate(loaded)


async def get_chapters(
    db: AsyncSession, world_id: uuid.UUID, manuscript_id: uuid.UUID, role: UserRole
) -> List[dict]:
    """Obtém os capítulos de um manuscrito sanitizados pelo Fog of War."""
    stmt = select(ManuscriptChapter).where(
        ManuscriptChapter.manuscript_id == manuscript_id
    ).order_by(ManuscriptChapter.order_index.asc())
    res = await db.execute(stmt)
    chapters = list(res.scalars().all())

    sanitized_chapters = []
    for ch in chapters:
        s_ch = sanitize_chapter_dict(ch, role)
        if s_ch is not None:
            sanitized_chapters.append(s_ch)

    return sanitized_chapters


async def create_chapter(
    db: AsyncSession,
    world_id: uuid.UUID,
    manuscript_id: uuid.UUID,
    role: UserRole,
    data: ManuscriptChapterCreate,
) -> dict:
    """Cria um novo capítulo em um manuscrito."""
    stmt_ms = select(Manuscript).where(Manuscript.id == manuscript_id, Manuscript.world_id == world_id)
    res_ms = await db.execute(stmt_ms)
    if not res_ms.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manuscrito não encontrado.",
        )

    visibility = data.visibility
    if visibility is None:
        visibility = VisibilityType.NULA if role == UserRole.MESTRE else VisibilityType.TOTAL

    chapter = ManuscriptChapter(
        manuscript_id=manuscript_id,
        title=data.title,
        content=data.content,
        order_index=data.order_index,
        visibility=visibility,
    )
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)

    return sanitize_chapter_dict(chapter, role)
