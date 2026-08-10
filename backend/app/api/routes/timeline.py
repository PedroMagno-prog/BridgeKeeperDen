"""Rotas do Modulo C: Linha do Tempo (Timeline) — 3 endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.world_access import WorldContext, get_world_ctx
from app.schemas.timeline import TimelineEraCreate, TimelineEraOut, TimelineOut
from app.services import timeline_service
from app.services.fog_of_war import sanitize_timeline_event

router = APIRouter()


# ── GET /worlds/{world_id}/timeline ───────────────────────────────────────────

@router.get("/", response_model=TimelineOut, summary="Timeline compilada do mundo")
async def obter_timeline(
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """
    Retorna eventos e eras organizados cronologicamente.
    Eventos sao artigos com in_game_sort_order preenchido.
    Fog of War: JOGADOR nao ve eventos NULA; PARCIAL mostra titulo mas is_locked=True.
    """
    # 1. Buscar eventos (artigos com data in-game)
    articles = await timeline_service.obter_eventos(db, ctx.world_id, ctx.role)

    events = []
    for article in articles:
        sanitized = sanitize_timeline_event(article, ctx.role)
        if sanitized is not None:
            events.append(sanitized)

    # 2. Buscar eras
    eras = await timeline_service.listar_eras(db, ctx.world_id)

    return TimelineOut(
        eras=[TimelineEraOut.model_validate(era) for era in eras],
        timeline_events=events,
    )


# ── POST /worlds/{world_id}/timeline/eras ─────────────────────────────────────

@router.post(
    "/eras",
    response_model=TimelineEraOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma era historica",
)
async def criar_era(
    body: TimelineEraCreate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Cria uma nova era/divisor na timeline. Apenas MESTRE."""
    if not ctx.is_mestre:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o Mestre pode criar eras.",
        )

    era = await timeline_service.criar_era(
        db,
        ctx.world_id,
        title=body.title,
        start_sort_order=body.start_sort_order,
        end_sort_order=body.end_sort_order,
    )
    await db.commit()
    await db.refresh(era)
    return era


# ── DELETE /worlds/{world_id}/timeline/eras/{era_id} ──────────────────────────

@router.delete(
    "/eras/{era_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma era",
)
async def deletar_era(
    era_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Remove uma era historica. Apenas MESTRE."""
    if not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode remover eras.")

    deleted = await timeline_service.deletar_era(db, era_id, ctx.world_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Era nao encontrada.")
    await db.commit()
