"""
Servico assincrono de Map.

CRUD de mapas, camadas e marcadores (pins).
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.enums import VisibilityType
from app.db.models.map import Map
from app.db.models.map_layer import MapLayer
from app.db.models.map_pin import MapPin


async def criar_mapa(
    db: AsyncSession,
    world_id: uuid.UUID,
    *,
    title: str,
    image_url: str,
) -> Map:
    """Cria um novo mapa."""
    mapa = Map(world_id=world_id, title=title, image_url=image_url)
    db.add(mapa)
    await db.flush()
    return mapa


async def listar_mapas(
    db: AsyncSession,
    world_id: uuid.UUID,
) -> Sequence[Map]:
    """Lista todos os mapas de um mundo."""
    result = await db.execute(
        select(Map)
        .where(Map.world_id == world_id)
        .order_by(Map.created_at.desc())
    )
    return result.scalars().all()


async def buscar_mapa(
    db: AsyncSession,
    map_id: uuid.UUID,
    world_id: uuid.UUID,
) -> Map | None:
    """Busca um mapa com layers e pins carregados."""
    stmt = (
        select(Map)
        .options(
            selectinload(Map.layers),
            selectinload(Map.pins),
        )
        .where(Map.id == map_id, Map.world_id == world_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def criar_layer(
    db: AsyncSession,
    map_id: uuid.UUID,
    *,
    name: str,
    is_default_active: bool = True,
) -> MapLayer:
    """Cria uma nova camada no mapa."""
    layer = MapLayer(map_id=map_id, name=name, is_default_active=is_default_active)
    db.add(layer)
    await db.flush()
    return layer


async def criar_pin(
    db: AsyncSession,
    map_id: uuid.UUID,
    *,
    title: str,
    x_position: Decimal,
    y_position: Decimal,
    icon: str = "default-pin",
    color: str = "#FF0000",
    visibility: VisibilityType = VisibilityType.NULA,
    layer_id: uuid.UUID | None = None,
    target_article_id: uuid.UUID | None = None,
    target_map_id: uuid.UUID | None = None,
) -> MapPin:
    """Cria um novo marcador no mapa."""
    pin = MapPin(
        map_id=map_id,
        title=title,
        x_position=x_position,
        y_position=y_position,
        icon=icon,
        color=color,
        visibility=visibility,
        layer_id=layer_id,
        target_article_id=target_article_id,
        target_map_id=target_map_id,
    )
    db.add(pin)
    await db.flush()
    return pin


async def buscar_pin(
    db: AsyncSession,
    pin_id: uuid.UUID,
    map_id: uuid.UUID,
) -> MapPin | None:
    """Busca um pin especifico."""
    result = await db.execute(
        select(MapPin).where(MapPin.id == pin_id, MapPin.map_id == map_id)
    )
    return result.scalar_one_or_none()


async def atualizar_pin(
    db: AsyncSession,
    pin: MapPin,
    **kwargs,
) -> MapPin:
    """Atualiza campos de um pin."""
    for campo, valor in kwargs.items():
        if valor is not None:
            setattr(pin, campo, valor)
    await db.flush()
    return pin
