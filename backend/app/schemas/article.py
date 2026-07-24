from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

from app.db.models.enums import VisibilityType


# ── Seções ───────────────────────────────────────────────────────────────────
class ArticleSectionCreate(BaseModel):
    title: str
    content: str = ""
    order_index: int = 0


class ArticleSectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    article_id: uuid.UUID
    title: str
    content: str
    order_index: int


# ── Mochila / Inventário ──────────────────────────────────────────────────────
class CharacterInventoryCreate(BaseModel):
    item_name: str
    quantity: int = 1
    description: Optional[str] = None


class CharacterInventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    article_id: uuid.UUID
    item_name: str
    quantity: int
    description: Optional[str] = None


# ── Artigos ──────────────────────────────────────────────────────────────────
class ArticleCreate(BaseModel):
    title: str
    visibility: Optional[VisibilityType] = None  # Se omitido, injetado pelo service conforme role
    in_game_date: Optional[str] = None
    in_game_sort_order: Optional[int] = None
    tags: List[str] = []
    sections: List[ArticleSectionCreate] = []


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    visibility: Optional[VisibilityType] = None
    in_game_date: Optional[str] = None
    in_game_sort_order: Optional[int] = None
    tags: Optional[List[str]] = None
    sections: Optional[List[ArticleSectionCreate]] = None


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    world_id: uuid.UUID
    title: str
    visibility: VisibilityType
    in_game_date: Optional[str] = None
    in_game_sort_order: Optional[int] = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_locked: bool = False
    tags: List[str] = []
    sections: List[ArticleSectionResponse] = []
    inventory_items: List[CharacterInventoryResponse] = []
