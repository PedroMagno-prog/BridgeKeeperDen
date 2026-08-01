"""Schemas Pydantic para Timeline e TimelineEra."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.db.models.enums import VisibilityType


# ── Inputs ────────────────────────────────────────────────────────────────────

class TimelineEraCreate(BaseModel):
    """Input para criacao de uma era historica."""
    title: str = Field(..., min_length=1, max_length=100)
    start_sort_order: int
    end_sort_order: int


# ── Outputs ───────────────────────────────────────────────────────────────────

class TimelineEraOut(BaseModel):
    id: uuid.UUID
    title: str
    start_sort_order: int
    end_sort_order: int

    model_config = {"from_attributes": True}


class TimelineEventOut(BaseModel):
    article_id: uuid.UUID
    title: str
    in_game_date: str | None
    in_game_sort_order: int | None
    visibility: VisibilityType
    is_locked: bool = False


class TimelineOut(BaseModel):
    """Resposta completa da timeline."""
    eras: list[TimelineEraOut]
    timeline_events: list[TimelineEventOut]
