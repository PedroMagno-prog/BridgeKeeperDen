"""Schemas Pydantic para Article, ArticleFolder, ArticleTag e CharacterInventory."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import VisibilityType


# ── Pastas (ArticleFolder) ───────────────────────────────────────────────────

class ArticleFolderCreate(BaseModel):
    """Input para criação de uma pasta de artigos."""
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: int | None = None


class ArticleFolderUpdate(BaseModel):
    """Input para atualização de uma pasta de artigos."""
    name: str | None = Field(None, min_length=1, max_length=255)
    parent_id: int | None = None


class ArticleFolderOut(BaseModel):
    """Output de dados de uma pasta de artigos."""
    id: int
    world_id: uuid.UUID
    parent_id: int | None = None
    name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Inputs de Artigo ──────────────────────────────────────────────────────────

class SectionInput(BaseModel):
    """Input legado para seção (compatibilidade)."""
    id: str | None = None
    title: str = Field(..., min_length=1, max_length=150)
    content: str = Field("", max_length=50_000)
    order_index: int = Field(0, ge=0)


class ArticleCreate(BaseModel):
    """Input para criação de um artigo."""
    title: str = Field(..., min_length=1, max_length=150)
    folder_id: int | None = None
    content: str = Field("", max_length=500_000)
    visibility: VisibilityType | None = None  # default depende do role (RN-01/RN-02)
    in_game_date: str | None = Field(None, max_length=50)
    in_game_sort_order: int | None = None
    tags: list[str] = Field(default_factory=list)
    sections: list[SectionInput] | None = None


class ArticleUpdate(BaseModel):
    """Input para atualização de um artigo."""
    title: str | None = Field(None, min_length=1, max_length=150)
    folder_id: int | None = None
    content: str | None = Field(None, max_length=500_000)
    visibility: VisibilityType | None = None
    in_game_date: str | None = Field(None, max_length=50)
    in_game_sort_order: int | None = None
    tags: list[str] | None = None
    sections: list[SectionInput] | None = None


class ArticleContentUpdate(BaseModel):
    """Payload para atualização parcial do conteúdo Markdown (autosave acelerado)."""
    content: str = Field(..., max_length=500_000)


class InventoryItemInput(BaseModel):
    """Input para um item de inventário."""
    item_name: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(1, ge=0)
    description: str | None = Field(None, max_length=2000)


class InventoryUpdateInput(BaseModel):
    """Input para atualização completa do inventário."""
    items: list[InventoryItemInput]


# ── Outputs de Artigo ─────────────────────────────────────────────────────────

class SectionOut(BaseModel):
    id: str
    title: str
    content: str
    order_index: int
    image_url: str | None = None


class InventoryItemOut(BaseModel):
    id: uuid.UUID
    item_name: str
    quantity: int
    description: str | None


class ArticleListOut(BaseModel):
    """Artigo em listagem."""
    id: uuid.UUID
    folder_id: int | None = None
    title: str
    visibility: VisibilityType
    in_game_date: str | None = None
    in_game_sort_order: int | None = None
    tags: list[str] = []
    created_by: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_locked: bool = False
    can_edit: bool = True
    can_delete: bool = True


class ArticleDetailOut(BaseModel):
    """Artigo em detalhe."""
    id: uuid.UUID
    folder_id: int | None = None
    title: str
    content: str = ""
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
    can_edit: bool = True
    can_delete: bool = True


# ── Wikilinks & Menções ───────────────────────────────────────────────────────

class ArticleResolveOut(BaseModel):
    """Resultado da resolução rápida de um Wikilink por título."""
    exists: bool
    article_id: uuid.UUID | None = None
    title: str
    visibility: VisibilityType | None = None
    is_locked: bool = False


class MentionSuggestionOut(BaseModel):
    """Sugestão de artigo para o menu de autocomplete de menções."""
    id: uuid.UUID
    title: str
    visibility: VisibilityType
    tags: list[str] = []


class BacklinkOut(BaseModel):
    """Informação de uma citação (backlink) que aponta para um artigo."""
    article_id: uuid.UUID
    title: str
    visibility: VisibilityType
    section_title: str = ""
    snippet: str
    is_locked: bool = False


# ── Importação Obsidian ───────────────────────────────────────────────────────

class ObsidianImportResultOut(BaseModel):
    """Resultado da importação em lote de cofre Obsidian (.zip)."""
    imported_count: int
    skipped_count: int
    message: str
