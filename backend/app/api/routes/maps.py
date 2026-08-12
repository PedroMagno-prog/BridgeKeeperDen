"""Rotas do Modulo B: Mapas Interativos e Marcadores (Pins) — 5 endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.world_access import WorldContext, get_world_ctx
from app.schemas.map import (
    MapCreate,
    MapDetailOut,
    MapLayerCreate,
    MapLayerOut,
    MapListOut,
    MapPinCreate,
    MapPinOut,
    MapPinUpdate,
    MapUpdateInput,
)
from app.services import map_service
from app.services.fog_of_war import sanitize_pin

router = APIRouter()


# ── GET /worlds/{world_id}/maps ───────────────────────────────────────────────

@router.get("/", response_model=list[MapListOut], summary="Lista mapas do mundo")
async def listar_mapas(
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Lista todos os mapas cadastrados no mundo."""
    return await map_service.listar_mapas(db, ctx.world_id)


# ── POST /worlds/{world_id}/maps ──────────────────────────────────────────────

@router.post(
    "/",
    response_model=MapListOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo mapa",
)
async def criar_mapa(
    body: MapCreate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Cria um novo mapa. Apenas MESTRE."""
    if not ctx.is_mestre:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o Mestre pode criar mapas.",
        )

    mapa = await map_service.criar_mapa(
        db, ctx.world_id, title=body.title, image_url=body.image_url,
    )
    await db.commit()
    await db.refresh(mapa)
    return mapa


# ── PUT /worlds/{world_id}/maps/{map_id} ─────────────────────────────────────

@router.put(
    "/{map_id}",
    response_model=MapListOut,
    summary="Atualiza um mapa",
)
async def atualizar_mapa(
    map_id: uuid.UUID,
    body: MapUpdateInput,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Atualiza titulo e imagem do mapa. Apenas MESTRE."""
    if not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode editar mapas.")

    mapa = await map_service.buscar_mapa(db, map_id, ctx.world_id)
    if not mapa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapa nao encontrado.")

    await map_service.atualizar_mapa(db, mapa, title=body.title, image_url=body.image_url)
    await db.commit()
    await db.refresh(mapa)
    return mapa


# ── DELETE /worlds/{world_id}/maps/{map_id} ──────────────────────────────────

@router.delete(
    "/{map_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um mapa",
)
async def deletar_mapa(
    map_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Deleta um mapa e seus pins/layers. Apenas MESTRE."""
    if not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode deletar mapas.")

    mapa = await map_service.buscar_mapa(db, map_id, ctx.world_id)
    if not mapa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapa nao encontrado.")

    await map_service.deletar_mapa(db, mapa)
    await db.commit()


# ── GET /worlds/{world_id}/maps/{map_id} ─────────────────────────────────────

@router.get("/{map_id}", response_model=MapDetailOut, summary="Detalhe do mapa com layers e pins")
async def buscar_mapa(
    map_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """
    Obtem dados do mapa com layers e pins.
    Pins sao sanitizados pelo Fog of War.
    """
    mapa = await map_service.buscar_mapa(db, map_id, ctx.world_id)
    if not mapa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapa nao encontrado.")

    sanitized_pins = []
    for pin in mapa.pins:
        s = sanitize_pin(pin, ctx.role)
        if s is not None:
            sanitized_pins.append(s)

    return MapDetailOut(
        id=mapa.id,
        title=mapa.title,
        image_url=mapa.image_url,
        created_at=mapa.created_at,
        layers=[
            MapLayerOut(id=l.id, name=l.name, is_default_active=l.is_default_active)
            for l in mapa.layers
        ],
        pins=sanitized_pins,
    )


# ── POST /worlds/{world_id}/maps/{map_id}/layers ─────────────────────────────

@router.post(
    "/{map_id}/layers",
    response_model=MapLayerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma camada no mapa",
)
async def criar_layer(
    map_id: uuid.UUID,
    body: MapLayerCreate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Cria uma nova camada no mapa. Apenas MESTRE."""
    if not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode criar camadas.")

    mapa = await map_service.buscar_mapa(db, map_id, ctx.world_id)
    if not mapa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapa nao encontrado.")

    layer = await map_service.criar_layer(
        db, map_id, name=body.name, is_default_active=body.is_default_active,
    )
    await db.commit()
    await db.refresh(layer)
    return layer


# ── DELETE /worlds/{world_id}/maps/{map_id}/layers/{layer_id} ────────────────

@router.delete(
    "/{map_id}/layers/{layer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma camada do mapa",
)
async def deletar_layer(
    map_id: uuid.UUID,
    layer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Remove uma camada do mapa. Apenas MESTRE."""
    if not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode deletar camadas.")

    mapa = await map_service.buscar_mapa(db, map_id, ctx.world_id)
    if not mapa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapa nao encontrado.")

    layer = next((l for l in mapa.layers if l.id == layer_id), None)
    if not layer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camada nao encontrada.")

    await map_service.deletar_layer(db, layer)
    await db.commit()


# ── POST /worlds/{world_id}/maps/{map_id}/pins ───────────────────────────────

@router.post(
    "/{map_id}/pins",
    response_model=MapPinOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um marcador no mapa",
)
async def criar_pin(
    map_id: uuid.UUID,
    body: MapPinCreate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Cria um novo marcador no mapa. Apenas MESTRE."""
    if not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode criar marcadores.")

    mapa = await map_service.buscar_mapa(db, map_id, ctx.world_id)
    if not mapa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapa nao encontrado.")

    pin = await map_service.criar_pin(
        db,
        map_id,
        title=body.title,
        x_position=body.x_position,
        y_position=body.y_position,
        icon=body.icon,
        color=body.color,
        visibility=body.visibility,
        layer_id=body.layer_id,
        target_article_id=body.target_article_id,
        target_map_id=body.target_map_id,
    )
    await db.commit()
    
    # Recarrega o mapa para ter os relacionamentos target_article e target_map populados
    reloaded_map = await map_service.buscar_mapa(db, map_id, ctx.world_id)
    reloaded_pin = next((p for p in reloaded_map.pins if p.id == pin.id), pin)
    return sanitize_pin(reloaded_pin, ctx.role)


# ── PUT /worlds/{world_id}/maps/{map_id}/pins/{pin_id} ───────────────────────

@router.put(
    "/{map_id}/pins/{pin_id}",
    response_model=MapPinOut,
    summary="Atualiza um marcador",
)
async def atualizar_pin(
    map_id: uuid.UUID,
    pin_id: uuid.UUID,
    body: MapPinUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Atualiza posicao, icone, cor ou visibilidade de um marcador. Apenas MESTRE."""
    if not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode editar marcadores.")

    pin = await map_service.buscar_pin(db, pin_id, map_id)
    if not pin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marcador nao encontrado.")

    update_data = body.model_dump(exclude_unset=True)
    await map_service.atualizar_pin(db, pin, **update_data)
    await db.commit()

    reloaded_map = await map_service.buscar_mapa(db, map_id, ctx.world_id)
    reloaded_pin = next((p for p in reloaded_map.pins if p.id == pin.id), pin)
    return sanitize_pin(reloaded_pin, ctx.role)


# ── DELETE /worlds/{world_id}/maps/{map_id}/pins/{pin_id} ────────────────────

@router.delete(
    "/{map_id}/pins/{pin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um marcador do mapa",
)
async def deletar_pin(
    map_id: uuid.UUID,
    pin_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Remove um marcador. Apenas MESTRE."""
    if not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode deletar marcadores.")

    pin = await map_service.buscar_pin(db, pin_id, map_id)
    if not pin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marcador nao encontrado.")

    await map_service.deletar_pin(db, pin)
    await db.commit()
