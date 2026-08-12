"""Model de mundo/cenário (tabela `worlds`)."""
from __future__ import annotations

import secrets
import uuid

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db.session import Base


def generate_invite_code() -> str:
    """Gera um código de convite único de 10 caracteres (ex: 'k9X2mQ8pL1')."""
    return secrets.token_urlsafe(8)[:10]


class World(Base):
    """Contêiner isolado de um cenário/campanha."""

    __tablename__ = "worlds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    invite_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        default=generate_invite_code,
        index=True,
        comment="Código único para link de convite de jogadores",
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    owner: Mapped["User"] = relationship(
        "User", back_populates="owned_worlds",
    )
    members: Mapped[list["WorldMember"]] = relationship(
        "WorldMember",
        back_populates="world",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    articles: Mapped[list["Article"]] = relationship(
        "Article",
        back_populates="world",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    maps: Mapped[list["Map"]] = relationship(
        "Map",
        back_populates="world",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    manuscripts: Mapped[list["Manuscript"]] = relationship(
        "Manuscript",
        back_populates="world",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    timeline_eras: Mapped[list["TimelineEra"]] = relationship(
        "TimelineEra",
        back_populates="world",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<World id={self.id} name={self.name!r}>"
