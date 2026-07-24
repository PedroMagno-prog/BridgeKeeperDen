from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.models.enums import UserRole

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.article import Article
    from app.db.models.map import Map
    from app.db.models.manuscript import Manuscript
    from app.db.models.timeline import TimelineEra


class World(Base):
    """Contêiner isolado de um cenário/campanha de RPG."""

    __tablename__ = "worlds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relacionamentos
    owner: Mapped[User] = relationship(
        "User",
        back_populates="owned_worlds",
    )
    members: Mapped[List[WorldMember]] = relationship(
        "WorldMember",
        back_populates="world",
        cascade="all, delete-orphan",
    )
    articles: Mapped[List[Article]] = relationship(
        "Article",
        back_populates="world",
        cascade="all, delete-orphan",
    )
    maps: Mapped[List[Map]] = relationship(
        "Map",
        back_populates="world",
        cascade="all, delete-orphan",
    )
    manuscripts: Mapped[List[Manuscript]] = relationship(
        "Manuscript",
        back_populates="world",
        cascade="all, delete-orphan",
    )
    timeline_eras: Mapped[List[TimelineEra]] = relationship(
        "TimelineEra",
        back_populates="world",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<World id={self.id} name={self.name!r}>"


class WorldMember(Base):
    """Associação entre Usuário e Mundo, definindo o papel de Mestre ou Jogador."""

    __tablename__ = "world_members"
    __table_args__ = (
        UniqueConstraint("world_id", "user_id", name="unique_world_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_type=False),
        nullable=False,
        default=UserRole.JOGADOR,
    )

    # Relacionamentos
    world: Mapped[World] = relationship(
        "World",
        back_populates="members",
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="world_memberships",
    )

    def __repr__(self) -> str:
        return f"<WorldMember world_id={self.world_id} user_id={self.user_id} role={self.role}>"
