"""Schemas Pydantic para Quest e QuestObjective."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import VisibilityType
from app.db.models.quest import QuestCategory, QuestStatus


# ── Inputs ────────────────────────────────────────────────────────────────────

class ObjectiveInput(BaseModel):
    """Input para um objetivo de quest."""
    description: str = Field(..., min_length=1, max_length=255)
    is_completed: bool = False
    order_index: int = Field(0, ge=0)


class QuestCreate(BaseModel):
    """Input para criacao de uma quest."""
    title: str = Field(..., min_length=1, max_length=150)
    description: str = Field("", max_length=10_000)
    category: QuestCategory = QuestCategory.SIDE_QUEST
    status: QuestStatus = QuestStatus.NOT_STARTED
    visibility: VisibilityType | None = None
    rewards: str | None = Field(None, max_length=2000)
    article_id: uuid.UUID | None = None
    objectives: list[ObjectiveInput] = Field(default_factory=list)


class QuestUpdate(BaseModel):
    """Input para atualizacao de uma quest."""
    title: str | None = Field(None, min_length=1, max_length=150)
    description: str | None = Field(None, max_length=10_000)
    category: QuestCategory | None = None
    status: QuestStatus | None = None
    visibility: VisibilityType | None = None
    rewards: str | None = Field(None, max_length=2000)
    article_id: uuid.UUID | None = None
    objectives: list[ObjectiveInput] | None = None


# ── Outputs ───────────────────────────────────────────────────────────────────

class ObjectiveOut(BaseModel):
    id: uuid.UUID
    description: str
    is_completed: bool
    order_index: int


class QuestOut(BaseModel):
    id: uuid.UUID
    world_id: uuid.UUID
    title: str
    description: str
    category: QuestCategory
    status: QuestStatus
    visibility: VisibilityType
    rewards: str | None = None
    article_id: uuid.UUID | None = None
    article_title: str | None = None
    objectives: list[ObjectiveOut] = []
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_locked: bool = False
