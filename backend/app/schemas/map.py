from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.db.models.enums import VisibilityType


# ── Camadas (Layers) ─────────────────────────────────────────────────────────
class MapLayerCreate(BaseModel):
    name: str
    is_default_active: bool = True


class MapLayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    map_id: uuid.UUID
    name: str
    is_default_active: bool


# ── Marcadores (Pins) ─────────────────────────────────────────────────────────
class MapPinCreate(BaseModel):
    title: str
    x_position: float = Field(..., ge=0.0, le=100.0)
    y_position: float = Field(..., ge=0.0, le=100.0)
    layer_id: Optional[uuid.UUID] = None
    target_article_id: Optional[uuid.UUID] = None
    target_map_id: Optional[uuid.UUID] = None
    icon: str = "default-pin"
    color: str = "#FF0000"
    visibility: Optional[VisibilityType] = None


class MapPinUpdate(BaseModel):
    title: Optional[str] = None
    x_position: Optional[float] = Field(None, ge=0.0, le=100.0)
    y_position: Optional[float] = Field(None, ge=0.0, le=100.0)
    layer_id: Optional[uuid.UUID] = None
    target_article_id: Optional[uuid.UUID] = None
    target_map_id: Optional[uuid.UUID] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    visibility: Optional[VisibilityType] = None


class MapPinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    map_id: uuid.UUID
    layer_id: Optional[uuid.UUID] = None
    target_article_id: Optional[uuid.UUID] = None
    target_map_id: Optional[uuid.UUID] = None
    title: str
    x_position: float
    y_position: float
    icon: str
    color: str
    visibility: VisibilityType
    is_locked: bool = False


# ── Mapa ──────────────────────────────────────────────────────────────────────
class MapCreate(BaseModel):
    title: str
    image_url: str


class MapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    world_id: uuid.UUID
    title: str
    image_url: str
    created_at: datetime
    layers: List[MapLayerResponse] = []
    pins: List[MapPinResponse] = []
