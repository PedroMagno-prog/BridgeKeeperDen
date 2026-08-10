"""
Servico assincrono de Manuscript.

CRUD de manuscritos e capitulos com suporte a Fog of War.
"""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.enums import UserRole, VisibilityType
from app.db.models.manuscript import Manuscript
from app.db.models.manuscript_chapter import ManuscriptChapter


async def criar_manuscrito(
    db: AsyncSession,
    world_id: uuid.UUID,
    created_by: uuid.UUID,
    *,
    title: str,
) -> Manuscript:
    """Cria um novo manuscrito."""
    manuscript = Manuscript(
        world_id=world_id,
        title=title,
        created_by=created_by,
    )
    db.add(manuscript)
    await db.flush()
    return manuscript


async def listar_manuscritos(
    db: AsyncSession,
    world_id: uuid.UUID,
) -> Sequence[Manuscript]:
    """Lista todos os manuscritos de um mundo."""
    result = await db.execute(
        select(Manuscript)
        .where(Manuscript.world_id == world_id)
        .order_by(Manuscript.created_at.desc())
    )
    return result.scalars().all()


async def buscar_manuscrito(
    db: AsyncSession,
    manuscript_id: uuid.UUID,
    world_id: uuid.UUID,
) -> Manuscript | None:
    """Busca um manuscrito com chapters carregados."""
    stmt = (
        select(Manuscript)
        .options(selectinload(Manuscript.chapters))
        .where(Manuscript.id == manuscript_id, Manuscript.world_id == world_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def criar_capitulo(
    db: AsyncSession,
    manuscript_id: uuid.UUID,
    role: UserRole,
    *,
    title: str,
    content: str,
    order_index: int,
    visibility: VisibilityType | None,
) -> ManuscriptChapter:
    """
    Cria um novo capitulo.
    Aplica RN-01/RN-02 se visibility nao for informado.
    """
    if visibility is None:
        visibility = VisibilityType.NULA if role == UserRole.MESTRE else VisibilityType.TOTAL

    chapter = ManuscriptChapter(
        manuscript_id=manuscript_id,
        title=title,
        content=content,
        order_index=order_index,
        visibility=visibility,
    )
    db.add(chapter)
    await db.flush()
    return chapter


async def listar_capitulos(
    db: AsyncSession,
    manuscript_id: uuid.UUID,
    role: UserRole,
) -> Sequence[ManuscriptChapter]:
    """
    Lista capitulos de um manuscrito.
    JOGADOR: filtra NULA no nivel de query (RNF-03).
    """
    stmt = (
        select(ManuscriptChapter)
        .where(ManuscriptChapter.manuscript_id == manuscript_id)
    )

    if role == UserRole.JOGADOR:
        stmt = stmt.where(ManuscriptChapter.visibility != VisibilityType.NULA)

    stmt = stmt.order_by(ManuscriptChapter.order_index.asc())

    result = await db.execute(stmt)
    return result.scalars().all()


async def buscar_capitulo(
    db: AsyncSession,
    chapter_id: uuid.UUID,
    manuscript_id: uuid.UUID,
) -> ManuscriptChapter | None:
    """Busca um capitulo pelo ID."""
    result = await db.execute(
        select(ManuscriptChapter).where(
            ManuscriptChapter.id == chapter_id,
            ManuscriptChapter.manuscript_id == manuscript_id,
        )
    )
    return result.scalar_one_or_none()


async def atualizar_capitulo(
    db: AsyncSession,
    chapter: ManuscriptChapter,
    *,
    title: str | None = None,
    content: str | None = None,
    order_index: int | None = None,
    visibility: VisibilityType | None = None,
) -> ManuscriptChapter:
    """Atualiza campos de um capitulo."""
    if title is not None:
        chapter.title = title
    if content is not None:
        chapter.content = content
    if order_index is not None:
        chapter.order_index = order_index
    if visibility is not None:
        chapter.visibility = visibility
    await db.flush()
    return chapter

