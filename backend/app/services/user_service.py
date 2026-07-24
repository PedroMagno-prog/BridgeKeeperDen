"""Serviço assíncrono de User."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_senha
from app.db.models.user import User


class EmailJaCadastradoError(Exception):
    """Lançada quando o e-mail já existe no banco."""


class UsernameJaCadastradoError(Exception):
    """Lançada quando o username já existe no banco."""


async def criar_usuario(
    db: AsyncSession, username: str, email: str, password: str,
) -> User:
    """Cria e persiste um novo usuário com senha hashed."""
    # Verifica email duplicado
    existente = await db.execute(
        select(User).where(User.email == email)
    )
    if existente.scalar_one_or_none():
        raise EmailJaCadastradoError(f"E-mail '{email}' já está em uso.")

    # Verifica username duplicado
    existente = await db.execute(
        select(User).where(User.username == username)
    )
    if existente.scalar_one_or_none():
        raise UsernameJaCadastradoError(f"Username '{username}' já está em uso.")

    user = User(username=username, email=email, password_hash=hash_senha(password))
    db.add(user)
    await db.flush()
    return user


async def buscar_por_email(db: AsyncSession, email: str) -> User | None:
    resultado = await db.execute(
        select(User).where(User.email == email)
    )
    return resultado.scalar_one_or_none()


async def buscar_por_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    resultado = await db.execute(
        select(User).where(User.id == user_id)
    )
    return resultado.scalar_one_or_none()
