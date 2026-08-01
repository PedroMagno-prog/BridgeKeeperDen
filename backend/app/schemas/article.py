"""Schemas Pydantic para Article, ArticleSection, ArticleTag e CharacterInventory."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import VisibilityType


# ── Inputs ────────────────────────────────────────────────────────────────────

class SectionInput(BaseModel):
    """Input para criacao/atualizacao de uma secao."""
    title: str = Field(..., min_length=1, max_length=150)
    content: str = Field("", max_length=50_000)
    order_index: int = Field(0, ge=0)


class ArticleCreate(BaseModel):
    """Input para criacao de um artigo."""
    title: str = Field(..., min_length=1, max_length=150)
    visibility: VisibilityType | None = None  # default depende do role (RN-01/RN-02)
    in_game_date: str | None = Field(None, max_length=50)
    in_game_sort_order: int | None = None
    tags: list[str] = Field(default_factory=list)
    sections: list[SectionInput] = Field(default_factory=list)


class ArticleUpdate(BaseModel):
    """Input para atualizacao de um artigo."""
    title: str | None = Field(None, min_length=1, max_length=150)
    visibility: VisibilityType | None = None
    in_game_date: str | None = Field(None, max_length=50)
    in_game_sort_order: int | None = None
    tags: list[str] | None = None
    sections: list[SectionInput] | None = None


class InventoryItemInput(BaseModel):
    """Input para um item de inventario."""
    item_name: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(1, ge=0)
    description: str | None = Field(None, max_length=2000)


class InventoryUpdateInput(BaseModel):
    """Input para atualizacao completa do inventario."""
    items: list[InventoryItemInput]


# ── Outputs ───────────────────────────────────────────────────────────────────

class SectionOut(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    order_index: int


class InventoryItemOut(BaseModel):
    id: uuid.UUID
    item_name: str
    quantity: int
    description: str | None


class ArticleListOut(BaseModel):
    """Artigo em listagem (sem sections)."""
    id: uuid.UUID
    title: str
    visibility: VisibilityType
    in_game_date: str | None = None
    in_game_sort_order: int | None = None
    tags: list[str] = []
    created_by: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_locked: bool = False


class ArticleDetailOut(BaseModel):
    """Artigo em detalhe (com sections e inventory)."""
    id: uuid.UUID
    title: str
    visibility: VisibilityType
    in_game_date: str | None = None
    in_game_sort_order: int | None = None
    tags: list[str] = []
    sections: list[SectionOut] = []
    inventory_items: list[InventoryItemOut] = []
    created_by: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_locked: bool = False
