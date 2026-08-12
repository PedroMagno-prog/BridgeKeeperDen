"""Schemas Pydantic para Grupos de Inventário, Inventários e Itens."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import VisibilityType


# ── Items ─────────────────────────────────────────────────────────────────────

class InventoryItemCreate(BaseModel):
    """Input para criação de um item de inventário."""
    article_id: uuid.UUID | None = None
    custom_name: str | None = Field(None, max_length=100)
    quantity: int = Field(1, ge=0)
    notes: str | None = Field(None, max_length=2000)
    order_index: int = Field(0, ge=0)


class InventoryItemUpdate(BaseModel):
    """Input para atualização de um item de inventário."""
    article_id: uuid.UUID | None = None
    custom_name: str | None = Field(None, max_length=100)
    quantity: int | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=2000)
    order_index: int | None = Field(None, ge=0)


class ArticleItemSummaryOut(BaseModel):
    """Resumo básico do artigo vinculado para exibição no item de inventário."""
    id: uuid.UUID
    title: str
    visibility: VisibilityType
    tags: list[str] = []


class InventoryItemOut(BaseModel):
    """Output de um item de inventário."""
    id: uuid.UUID
    inventory_id: uuid.UUID
    article_id: uuid.UUID | None = None
    custom_name: str | None = None
    display_name: str  # Nome exibido (custom_name ou title do artigo)
    quantity: int
    notes: str | None = None
    order_index: int
    created_at: datetime
    article: ArticleItemSummaryOut | None = None


# ── Inventories ───────────────────────────────────────────────────────────────

class InventoryCreate(BaseModel):
    """Input para criação de um inventário."""
    group_id: uuid.UUID | None = None
    owner_article_id: uuid.UUID | None = None
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)
    limit: int | None = Field(None, ge=0)
    visibility: VisibilityType | None = None  # default depende do role


class InventoryUpdate(BaseModel):
    """Input para atualização de um inventário."""
    group_id: uuid.UUID | None = None
    owner_article_id: uuid.UUID | None = None
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)
    limit: int | None = Field(None, ge=0)
    visibility: VisibilityType | None = None


class InventoryOut(BaseModel):
    """Resumo em lista de um inventário."""
    id: uuid.UUID
    world_id: uuid.UUID
    group_id: uuid.UUID | None = None
    owner_article_id: uuid.UUID | None = None
    name: str
    description: str | None = None
    limit: int | None = None
    visibility: VisibilityType
    items_count: int = 0
    is_over_limit: bool = False
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class InventoryDetailOut(InventoryOut):
    """Detalhe completo de um inventário contendo seus itens."""
    items: list[InventoryItemOut] = []


# ── Groups ────────────────────────────────────────────────────────────────────

class InventoryGroupCreate(BaseModel):
    """Input para criação de um grupo de inventários."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)
    visibility: VisibilityType | None = None
    icon: str | None = Field("folder", max_length=50)


class InventoryGroupUpdate(BaseModel):
    """Input para atualização de um grupo de inventários."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)
    visibility: VisibilityType | None = None
    icon: str | None = Field(None, max_length=50)


class InventoryGroupOut(BaseModel):
    """Resumo de um grupo de inventários."""
    id: uuid.UUID
    world_id: uuid.UUID
    name: str
    description: str | None = None
    visibility: VisibilityType
    icon: str | None = None
    inventories_count: int = 0
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class InventoryGroupDetailOut(InventoryGroupOut):
    """Detalhe completo de um grupo contendo seus inventários e itens agregados."""
    inventories: list[InventoryDetailOut] = []
