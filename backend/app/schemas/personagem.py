"""Schemas Pydantic para Personagem."""
from __future__ import annotations
from pydantic import BaseModel, Field


class PersonagemCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=150)
    classe: str = Field(..., min_length=1, max_length=100)
    raca: str = Field(..., min_length=1, max_length=100)


class PersonagemUpdate(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=150)
    classe: str | None = Field(None, min_length=1, max_length=100)
    raca: str | None = Field(None, min_length=1, max_length=100)


class PersonagemOut(BaseModel):
    id: int
    nome: str
    classe: str
    raca: str
    jogador_id: int

    model_config = {"from_attributes": True}
