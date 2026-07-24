from __future__ import annotations

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.security import hash_senha, verificar_senha, criar_access_token
from app.db.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse


async def register_user(db: AsyncSession, data: UserRegister) -> UserResponse:
    """Registra uma nova conta de usuário."""
    # Verifica email existente
    stmt_email = select(User).where(User.email == data.email)
    res_email = await db.execute(stmt_email)
    if res_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado.",
        )

    # Verifica username existente
    stmt_user = select(User).where(User.username == data.username)
    res_user = await db.execute(stmt_user)
    if res_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já em uso.",
        )

    pwd_hash = hash_senha(data.password)
    new_user = User(
        username=data.username,
        email=data.email,
        password_hash=pwd_hash,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse.model_validate(new_user)


async def authenticate_user(db: AsyncSession, data: UserLogin) -> Token:
    """Autentica o usuário e gera token JWT."""
    stmt = select(User).where(User.email == data.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verificar_senha(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = criar_access_token({"sub": str(user.id)})
    return Token(access_token=token, token_type="bearer")
