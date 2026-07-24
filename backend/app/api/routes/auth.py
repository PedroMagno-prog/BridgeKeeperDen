"""Rotas de autenticação: login e cadastro."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.core.security import criar_access_token, verificar_senha
from app.schemas.user import LoginInput, TokenOut, UserCreate, UserOut
from app.services import user_service
from app.services.user_service import EmailJaCadastradoError, UsernameJaCadastradoError

router = APIRouter()


@router.post("/login", response_model=TokenOut, summary="Login com e-mail e senha")
async def login(body: LoginInput, db: AsyncSession = Depends(get_db)):
    user = await user_service.buscar_por_email(db, body.email)

    if not user or not verificar_senha(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )

    token = criar_access_token({"sub": str(user.id)})
    return TokenOut(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.post(
    "/register",
    response_model=TokenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria nova conta e retorna token",
)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.criar_usuario(
            db, body.username, body.email, body.password,
        )
        await db.commit()
        await db.refresh(user)
    except EmailJaCadastradoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except UsernameJaCadastradoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    token = criar_access_token({"sub": str(user.id)})
    return TokenOut(
        access_token=token,
        user=UserOut.model_validate(user),
    )
