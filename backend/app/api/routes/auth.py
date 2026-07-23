"""Rotas de autenticação: login e cadastro."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.core.security import criar_access_token, verificar_senha
from app.schemas.usuario import LoginInput, TokenOut, UsuarioCreate, UsuarioOut
from app.services import usuario_service
from app.services.usuario_service import EmailJaCadastradoError

router = APIRouter()


@router.post("/login", response_model=TokenOut, summary="Login com e-mail e senha")
async def login(body: LoginInput, db: AsyncSession = Depends(get_db)):
    usuario = await usuario_service.buscar_por_email(db, body.email)

    if not usuario or not verificar_senha(body.senha, usuario.senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )

    token = criar_access_token({"sub": str(usuario.id)})
    return TokenOut(
        access_token=token,
        usuario=UsuarioOut.model_validate(usuario),
    )


@router.post(
    "/cadastro",
    response_model=TokenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria nova conta e retorna token",
)
async def cadastro(body: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    try:
        usuario = await usuario_service.criar_usuario(
            db, body.nome, body.email, body.senha
        )
        await db.commit()
        await db.refresh(usuario)
    except EmailJaCadastradoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    token = criar_access_token({"sub": str(usuario.id)})
    return TokenOut(
        access_token=token,
        usuario=UsuarioOut.model_validate(usuario),
    )
