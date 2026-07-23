"""Schemas Pydantic para Usuario."""
from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field


class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    senha: str = Field(..., min_length=6, max_length=128)


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str

    model_config = {"from_attributes": True}


class LoginInput(BaseModel):
    email: EmailStr
    senha: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
