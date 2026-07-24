from __future__ import annotations

import uuid
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

from app.db.models.enums import VisibilityType


class TimelineEraCreate(BaseModel):
    title: str
    start_sort_order: int
    end_sort_order: int


class TimelineEraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    world_id: uuid.UUID
    title: str
    start_sort_order: int
    end_sort_order: int


class TimelineEventResponse(BaseModel):
    article_id: uuid.UUID
    title: str
    in_game_date: Optional[str] = None
    in_game_sort_order: Optional[int] = None
    visibility: VisibilityType
    snippet: Optional[str] = None
    is_locked: bool = False


class TimelineResponse(BaseModel):
    eras: List[TimelineEraResponse] = []
    timeline_events: List[TimelineEventResponse] = []
