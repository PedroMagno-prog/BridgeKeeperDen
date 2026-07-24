from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

from app.db.models.enums import VisibilityType


class ManuscriptChapterCreate(BaseModel):
    title: str
    content: str = ""
    order_index: int = 0
    visibility: Optional[VisibilityType] = None


class ManuscriptChapterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    manuscript_id: uuid.UUID
    title: str
    content: str
    order_index: int
    visibility: VisibilityType
    is_locked: bool = False


class ManuscriptCreate(BaseModel):
    title: str


class ManuscriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    world_id: uuid.UUID
    title: str
    created_by: uuid.UUID
    created_at: datetime
    chapters: List[ManuscriptChapterResponse] = []
