"""Schemas Pydantic para gestão detalhada de membros do mundo."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import UserRole


class MemberUpdateRoleInput(BaseModel):
    """Input para alterar a role de um membro."""
    role: UserRole


class DirectMemberAddInput(BaseModel):
    """Input para adicionar um membro diretamente via username ou e-mail."""
    user_id_or_email: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.JOGADOR


class MemberDetailOut(BaseModel):
    """Detalhes de um membro do mundo para o painel de gerenciamento."""
    id: uuid.UUID
    user_id: uuid.UUID
    username: str
    email: str
    role: UserRole
    joined_at: datetime | None = None
