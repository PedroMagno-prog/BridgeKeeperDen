from __future__ import annotations

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.db.models.map import Map, MapLayer, MapPin
from app.db.models.enums import UserRole, VisibilityType
from app.core.fog_of_war import sanitize_pin_dict
from app.schemas.map import MapCreate, MapResponse, MapPinCreate, MapPinUpdate, MapPinResponse


async def list_maps(db: AsyncSession, world_id: uuid.UUID) -> List[MapResponse]:
    """Lista os mapas cadastrados no mundo."""
    stmt = (
        select(Map)
        .options(selectinload(Map.layers))
        .where(Map.world_id == world_id)
        .order_by(Map.created_at.desc())
    )
    res = await db.execute(stmt)
    maps = list(res.scalars().all())
    return [MapResponse.model_validate(m) for m in maps]


async def create_map(db: AsyncSession, world_id: uuid.UUID, data: MapCreate) -> MapResponse:
    """Cadastra um novo mapa."""
    map_obj = Map(
        world_id=world_id,
        title=data.title,
        image_url=data.image_url,
    )
    db.add(map_obj)
    await db.flush()

    # Cria camada padrão "Geral"
    default_layer = MapLayer(
        map_id=map_obj.id,
        name="Geral",
        is_default_active=True,
    )
    db.add(default_layer)
    await db.commit()

    stmt = (
        select(Map)
        .options(selectinload(Map.layers), selectinload(Map.pins))
        .where(Map.id == map_obj.id)
    )
    res = await db.execute(stmt)
    loaded_map = res.scalar_one()
    return MapResponse.model_validate(loaded_map)


async def get_map_detail(
    db: AsyncSession, world_id: uuid.UUID, map_id: uuid.UUID, role: UserRole
) -> dict:
    """Obtém dados do mapa, camadas e pins sanitizados segundo o Fog of War."""
    stmt = (
        select(Map)
        .options(selectinload(Map.layers), selectinload(Map.pins))
        .where(Map.id == map_id, Map.world_id == world_id)
    )
    res = await db.execute(stmt)
    map_obj = res.scalar_one_or_none()

    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapa não encontrado.",
        )

    sanitized_pins = []
    for pin in map_obj.pins:
        s_pin = sanitize_pin_dict(pin, role)
        if s_pin is not None:
            sanitized_pins.append(s_pin)

    return {
        "id": map_obj.id,
        "world_id": map_obj.world_id,
        "title": map_obj.title,
        "image_url": map_obj.image_url,
        "created_at": map_obj.created_at,
        "layers": [
            {
                "id": l.id,
                "map_id": l.map_id,
                "name": l.name,
                "is_default_active": l.is_default_active,
            }
            for l in map_obj.layers
        ],
        "pins": sanitized_pins,
    }


async def create_pin(
    db: AsyncSession,
    world_id: uuid.UUID,
    map_id: uuid.UUID,
    role: UserRole,
    data: MapPinCreate,
) -> dict:
    """Cria um marcador (pin) no mapa."""
    stmt_map = select(Map).where(Map.id == map_id, Map.world_id == world_id)
    res_map = await db.execute(stmt_map)
    if not res_map.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapa não encontrado.",
        )

    visibility = data.visibility
    if visibility is None:
        visibility = VisibilityType.NULA if role == UserRole.MESTRE else VisibilityType.TOTAL

    pin = MapPin(
        map_id=map_id,
        layer_id=data.layer_id,
        target_article_id=data.target_article_id,
        target_map_id=data.target_map_id,
        title=data.title,
        x_position=data.x_position,
        y_position=data.y_position,
        icon=data.icon,
        color=data.color,
        visibility=visibility,
    )
    db.add(pin)
    await db.commit()
    await db.refresh(pin)

    return sanitize_pin_dict(pin, role)


async def update_pin(
    db: AsyncSession,
    world_id: uuid.UUID,
    map_id: uuid.UUID,
    pin_id: uuid.UUID,
    role: UserRole,
    data: MapPinUpdate,
) -> dict:
    """Atualiza a posição, ícone, cor ou visibilidade de um marcador."""
    stmt = select(MapPin).where(MapPin.id == pin_id, MapPin.map_id == map_id)
    res = await db.execute(stmt)
    pin = res.scalar_one_or_none()

    if not pin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Marcador não encontrado.",
        )

    if data.title is not None:
        pin.title = data.title
    if data.x_position is not None:
        pin.x_position = data.x_position
    if data.y_position is not None:
        pin.y_position = data.y_position
    if data.layer_id is not None:
        pin.layer_id = data.layer_id
    if data.target_article_id is not None:
        pin.target_article_id = data.target_article_id
    if data.target_map_id is not None:
        pin.target_map_id = data.target_map_id
    if data.icon is not None:
        pin.icon = data.icon
    if data.color is not None:
        pin.color = data.color
    if data.visibility is not None and role == UserRole.MESTRE:
        pin.visibility = data.visibility

    await db.commit()
    await db.refresh(pin)
    return sanitize_pin_dict(pin, role)
