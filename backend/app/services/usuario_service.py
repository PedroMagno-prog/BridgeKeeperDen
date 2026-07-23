"""Serviço assíncrono de Usuário."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_senha
from app.db.models.usuario import Usuario


class EmailJaCadastradoError(Exception):
    """Lançada quando o e-mail já existe no banco."""


async def criar_usuario(
    db: AsyncSession, nome: str, email: str, senha: str
) -> Usuario:
    """Cria e persiste um novo usuário com senha hashed."""
    existente = await db.execute(
        select(Usuario).where(Usuario.email == email)
    )
    if existente.scalar_one_or_none():
        raise EmailJaCadastradoError(f"E-mail '{email}' já está em uso.")

    usuario = Usuario(nome=nome, email=email, senha=hash_senha(senha))
    db.add(usuario)
    await db.flush()
    return usuario


async def buscar_por_email(db: AsyncSession, email: str) -> Usuario | None:
    resultado = await db.execute(
        select(Usuario).where(Usuario.email == email)
    )
    return resultado.scalar_one_or_none()


async def buscar_por_id(db: AsyncSession, usuario_id: int) -> Usuario | None:
    resultado = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    return resultado.scalar_one_or_none()
