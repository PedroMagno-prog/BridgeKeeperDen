"""Rotas do Modulo D: Manuscritos e Resumos de Sessao — 4 endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.world_access import WorldContext, get_world_ctx
from app.schemas.manuscript import ChapterCreate, ChapterOut, ChapterUpdate, ManuscriptCreate, ManuscriptOut
from app.services import manuscript_service
from app.services.fog_of_war import sanitize_chapter

router = APIRouter()


# ── GET /worlds/{world_id}/manuscripts ────────────────────────────────────────

@router.get("/", response_model=list[ManuscriptOut], summary="Lista manuscritos do mundo")
async def listar_manuscritos(
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Lista todos os manuscritos/diarios de sessao."""
    return await manuscript_service.listar_manuscritos(db, ctx.world_id)


# ── POST /worlds/{world_id}/manuscripts ───────────────────────────────────────

@router.post(
    "/",
    response_model=ManuscriptOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um manuscrito",
)
async def criar_manuscrito(
    body: ManuscriptCreate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Cria um novo manuscrito/diario de sessao."""
    manuscript = await manuscript_service.criar_manuscrito(
        db, ctx.world_id, ctx.user.id, title=body.title,
    )
    await db.commit()
    await db.refresh(manuscript)
    return manuscript


# ── GET /worlds/{world_id}/manuscripts/{manuscript_id}/chapters ───────────────

@router.get(
    "/{manuscript_id}/chapters",
    response_model=list[ChapterOut],
    summary="Lista capitulos de um manuscrito",
)
async def listar_capitulos(
    manuscript_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """
    Lista capitulos com filtragem por Fog of War.
    JOGADOR: nao ve capitulos NULA; PARCIAL retorna titulo mas content vazio.
    """
    manuscript = await manuscript_service.buscar_manuscrito(db, manuscript_id, ctx.world_id)
    if not manuscript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscrito nao encontrado.")

    chapters = await manuscript_service.listar_capitulos(db, manuscript_id, ctx.role)

    result = []
    for chapter in chapters:
        sanitized = sanitize_chapter(chapter, ctx.role)
        if sanitized is not None:
            result.append(sanitized)

    return result


# ── POST /worlds/{world_id}/manuscripts/{manuscript_id}/chapters ──────────────

@router.post(
    "/{manuscript_id}/chapters",
    response_model=ChapterOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um capitulo",
)
async def criar_capitulo(
    manuscript_id: uuid.UUID,
    body: ChapterCreate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """
    Cria um novo capitulo com suporte a @Mentions.
    RN-01: MESTRE -> visibility default NULA.
    RN-02: JOGADOR -> visibility default TOTAL.
    """
    manuscript = await manuscript_service.buscar_manuscrito(db, manuscript_id, ctx.world_id)
    if not manuscript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscrito nao encontrado.")

    chapter = await manuscript_service.criar_capitulo(
        db,
        manuscript_id,
        ctx.role,
        title=body.title,
        content=body.content,
        order_index=body.order_index,
        visibility=body.visibility,
    )
    await db.commit()
    await db.refresh(chapter)

    return ChapterOut(
        id=chapter.id,
        title=chapter.title,
        content=chapter.content,
        order_index=chapter.order_index,
        visibility=chapter.visibility,
        is_locked=False,
    )


# ── PUT /worlds/{world_id}/manuscripts/{manuscript_id}/chapters/{chapter_id} ──

@router.put(
    "/{manuscript_id}/chapters/{chapter_id}",
    response_model=ChapterOut,
    summary="Atualiza um capitulo",
)
async def atualizar_capitulo(
    manuscript_id: uuid.UUID,
    chapter_id: uuid.UUID,
    body: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Atualiza titulo, conteudo, visibilidade de um capitulo."""
    manuscript = await manuscript_service.buscar_manuscrito(db, manuscript_id, ctx.world_id)
    if not manuscript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscrito nao encontrado.")

    chapter = await manuscript_service.buscar_capitulo(db, chapter_id, manuscript_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capitulo nao encontrado.")

    # Apenas MESTRE pode alterar visibilidade
    if body.visibility is not None and not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode alterar a visibilidade.")

    await manuscript_service.atualizar_capitulo(
        db, chapter,
        title=body.title,
        content=body.content,
        order_index=body.order_index,
        visibility=body.visibility,
    )
    await db.commit()
    await db.refresh(chapter)

    return ChapterOut(
        id=chapter.id,
        title=chapter.title,
        content=chapter.content,
        order_index=chapter.order_index,
        visibility=chapter.visibility,
        is_locked=False,
    )

