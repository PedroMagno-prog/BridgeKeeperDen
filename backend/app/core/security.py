"""
Utilitários de segurança: hash de senha e geração/validação de JWT.

Bibliotecas utilizadas:
- bcrypt (hash de senha — mantida ativamente, sem dependências legadas)
- PyJWT  (tokens JWT — moderno, sem dependências criptográficas problemáticas)
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


# ── Hash de senha ──────────────────────────────────────────────────────────────

def hash_senha(senha_plain: str) -> str:
    """Retorna o hash bcrypt da senha em texto puro."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha_plain.encode(), salt).decode()


def verificar_senha(senha_plain: str, senha_hash: str) -> bool:
    """Verifica se a senha em texto puro corresponde ao hash armazenado."""
    return bcrypt.checkpw(senha_plain.encode(), senha_hash.encode())


# ── JWT ────────────────────────────────────────────────────────────────────────

def criar_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Gera um JWT assinado com HS256.

    Args:
        data: payload do token (ex: {"sub": str(user_id)})
        expires_delta: tempo de expiração customizado; usa o padrão do settings
                       se não for informado.

    Returns:
        String do token JWT.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    payload["exp"] = expire

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decodificar_token(token: str) -> dict:
    """
    Decodifica e valida um JWT.

    Raises:
        jwt.ExpiredSignatureError: token expirado.
        jwt.InvalidTokenError:    token inválido.

    Returns:
        Payload decodificado como dict.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
