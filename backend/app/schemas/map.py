"""Schemas Pydantic para Map, MapLayer e MapPin."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.db.models.enums import VisibilityType


# ── Inputs ────────────────────────────────────────────────────────────────────

class MapCreate(BaseModel):
    """Input para criacao de um mapa."""
    title: str = Field(..., min_length=1, max_length=100)
    image_url: str = Field(..., min_length=1, max_length=500)


class MapUpdateInput(BaseModel):
    """Input para atualizacao de um mapa."""
    title: str | None = Field(None, min_length=1, max_length=100)
    image_url: str | None = Field(None, min_length=1, max_length=500)


class MapLayerCreate(BaseModel):
    """Input para criacao de uma camada."""
    name: str = Field(..., min_length=1, max_length=50)
    is_default_active: bool = True


class MapPinCreate(BaseModel):
    """Input para criacao de um marcador."""
    title: str = Field(..., min_length=1, max_length=100)
    x_position: Decimal = Field(..., ge=0, le=100)
    y_position: Decimal = Field(..., ge=0, le=100)
    icon: str = Field("default-pin", max_length=50)
    color: str = Field("#FF0000", max_length=7)
    visibility: VisibilityType = VisibilityType.NULA
    layer_id: uuid.UUID | None = None
    target_article_id: uuid.UUID | None = None
    target_map_id: uuid.UUID | None = None


class MapPinUpdate(BaseModel):
    """Input para atualizacao de um marcador."""
    title: str | None = Field(None, min_length=1, max_length=100)
    x_position: Decimal | None = Field(None, ge=0, le=100)
    y_position: Decimal | None = Field(None, ge=0, le=100)
    icon: str | None = Field(None, max_length=50)
    color: str | None = Field(None, max_length=7)
    visibility: VisibilityType | None = None
    layer_id: uuid.UUID | None = None
    target_article_id: uuid.UUID | None = None
    target_map_id: uuid.UUID | None = None


# ── Outputs ───────────────────────────────────────────────────────────────────

class MapLayerOut(BaseModel):
    id: uuid.UUID
    name: str
    is_default_active: bool


class MapPinArticleSummary(BaseModel):
    """Resumo de artigo vinculado a um pino no mapa."""
    id: uuid.UUID
    title: str
    visibility: VisibilityType
    tags: list[str] = []
    first_section_preview: str | None = None


class MapPinOut(BaseModel):
    id: uuid.UUID
    title: str
    x_position: float
    y_position: float
    icon: str
    color: str
    visibility: VisibilityType
    layer_id: uuid.UUID | None = None
    target_article_id: uuid.UUID | None = None
    target_map_id: uuid.UUID | None = None
    target_article: MapPinArticleSummary | None = None
    target_map_title: str | None = None
    created_by: uuid.UUID | None = None
    is_locked: bool = False
    can_edit: bool = False
    can_delete: bool = False


class MapListOut(BaseModel):
    """Mapa em listagem (sem pins)."""
    id: uuid.UUID
    title: str
    image_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MapDetailOut(BaseModel):
    """Mapa em detalhe (com layers e pins sanitizados)."""
    id: uuid.UUID
    title: str
    image_url: str
    created_at: datetime
    layers: list[MapLayerOut] = []
    pins: list[MapPinOut] = []
