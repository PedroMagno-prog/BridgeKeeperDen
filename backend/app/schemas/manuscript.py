"""Schemas Pydantic para Manuscript e ManuscriptChapter."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import VisibilityType


# ── Inputs ────────────────────────────────────────────────────────────────────

class ManuscriptCreate(BaseModel):
    """Input para criacao de um manuscrito."""
    title: str = Field(..., min_length=1, max_length=150)


class ChapterCreate(BaseModel):
    """Input para criacao de um capitulo."""
    title: str = Field(..., min_length=1, max_length=150)
    content: str = Field("", max_length=100_000)
    order_index: int = Field(0, ge=0)
    visibility: VisibilityType | None = None  # default depende do role


class ChapterUpdate(BaseModel):
    """Input para atualizacao parcial de um capitulo."""
    title: str | None = Field(None, min_length=1, max_length=150)
    content: str | None = Field(None, max_length=100_000)
    order_index: int | None = Field(None, ge=0)
    visibility: VisibilityType | None = None



# ── Outputs ───────────────────────────────────────────────────────────────────

class ManuscriptOut(BaseModel):
    """Representacao publica de um manuscrito."""
    id: uuid.UUID
    title: str
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ChapterOut(BaseModel):
    """Representacao de um capitulo (sanitizado pelo Fog of War)."""
    id: uuid.UUID
    title: str
    content: str
    order_index: int
    visibility: VisibilityType
    is_locked: bool = False
