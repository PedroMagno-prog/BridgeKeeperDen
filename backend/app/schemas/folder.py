"""Schemas Pydantic para Pastas (ArticleFolder) e Árvore Hierárquica do Codex."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import VisibilityType


class FolderCreate(BaseModel):
    """Input para criação de uma pasta de artigos."""
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: int | None = None


class FolderUpdate(BaseModel):
    """Input para atualização de uma pasta de artigos."""
    name: str | None = Field(None, min_length=1, max_length=255)
    parent_id: int | None = None


class FolderResponse(BaseModel):
    """Output basico de uma pasta."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    world_id: uuid.UUID
    name: str
    parent_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ArticleSummarySchema(BaseModel):
    """Resumo simplificado de um artigo para exibição na árvore de pastas."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    folder_id: int | None = None
    visibility: VisibilityType
    in_game_date: str | None = None
    updated_at: datetime | None = None
    is_locked: bool = False
    can_edit: bool = True
    can_delete: bool = True


class FolderTreeResponse(BaseModel):
    """Estrutura hierárquica recursiva de uma pasta contendo subpastas e artigos."""
    id: int
    name: str
    parent_id: int | None = None
    children: list[FolderTreeResponse] = Field(default_factory=list)
    articles: list[ArticleSummarySchema] = Field(default_factory=list)


class WorldFolderTreeResponse(BaseModel):
    """Árvore completa do mundo contendo pastas raiz e artigos sem pasta."""
    folders: list[FolderTreeResponse] = Field(default_factory=list)
    root_articles: list[ArticleSummarySchema] = Field(default_factory=list)
