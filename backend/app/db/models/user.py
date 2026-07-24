"""Model de usuário da plataforma (tabela `users`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db.session import Base


class User(Base):
    """Conta de acesso à plataforma."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Hash bcrypt/argon2 da senha",
    )
    created_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    owned_worlds: Mapped[list["World"]] = relationship(
        "World",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    memberships: Mapped[list["WorldMember"]] = relationship(
        "WorldMember",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"
