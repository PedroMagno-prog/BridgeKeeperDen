from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.world import World, WorldMember
    from app.db.models.article import Article
    from app.db.models.manuscript import Manuscript


class User(Base):
    """Modelo de usuário do sistema."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relacionamentos
    owned_worlds: Mapped[List[World]] = relationship(
        "World",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    world_memberships: Mapped[List[WorldMember]] = relationship(
        "WorldMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    articles: Mapped[List[Article]] = relationship(
        "Article",
        back_populates="creator",
    )
    manuscripts: Mapped[List[Manuscript]] = relationship(
        "Manuscript",
        back_populates="creator",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} email={self.email!r}>"
