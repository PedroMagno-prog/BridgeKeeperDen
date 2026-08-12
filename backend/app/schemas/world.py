"""Schemas Pydantic para World e WorldMember."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import UserRole


class WorldCreate(BaseModel):
    """Input para criação de um mundo."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)


class WorldOut(BaseModel):
    """Representação pública de um mundo."""
    id: uuid.UUID
    name: str
    description: str | None
    invite_code: str
    owner_id: uuid.UUID
    created_at: datetime
    role: UserRole | None = None  # papel do usuário logado neste mundo

    model_config = {"from_attributes": True}


class WorldInviteInfoOut(BaseModel):
    """Informações públicas do mundo exibidas na tela de convite /join/:code."""
    invite_code: str
    world_id: uuid.UUID
    world_name: str
    world_description: str | None
    owner_username: str
    members_count: int


class WorldMemberOut(BaseModel):
    """Representação pública de um membro do mundo."""
    id: uuid.UUID
    world_id: uuid.UUID
    user_id: uuid.UUID
    role: UserRole

    model_config = {"from_attributes": True}


class WorldMemberAdd(BaseModel):
    """Input para adicionar um membro ao mundo."""
    user_id: uuid.UUID
    role: UserRole = UserRole.JOGADOR
