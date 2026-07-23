"""Dependência de autenticação via JWT para rotas protegidas."""
from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.core.security import decodificar_token
from app.db.models.usuario import Usuario
from app.services import usuario_service

bearer_scheme = HTTPBearer(auto_error=True)

_UNAUTH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token inválido ou expirado.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """
    Extrai e valida o JWT do header Authorization: Bearer <token>.
    Retorna o objeto Usuario autenticado.
    """
    try:
        payload = decodificar_token(credentials.credentials)
        user_id: int = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _UNAUTH

    usuario = await usuario_service.buscar_por_id(db, user_id)
    if not usuario:
        raise _UNAUTH

    return usuario
