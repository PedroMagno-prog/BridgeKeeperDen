"""Schemas Pydantic para User."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Input para criação de conta."""
    username: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserOut(BaseModel):
    """Representação pública do usuário (sem senha)."""
    id: uuid.UUID
    username: str
    email: str

    model_config = {"from_attributes": True}


class LoginInput(BaseModel):
    """Input para login."""
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    """Resposta de autenticação com token JWT."""
    access_token: str
    token_type: str = "bearer"
    user: UserOut
