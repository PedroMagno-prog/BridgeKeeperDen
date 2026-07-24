from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

from app.db.models.enums import UserRole


class WorldCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorldMemberCreate(BaseModel):
    user_id: uuid.UUID
    role: UserRole = UserRole.JOGADOR


class WorldMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    world_id: uuid.UUID
    user_id: uuid.UUID
    role: UserRole


class WorldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    owner_id: uuid.UUID
    user_role: Optional[UserRole] = None
    created_at: datetime
