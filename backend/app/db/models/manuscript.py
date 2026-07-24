from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.models.enums import VisibilityType

if TYPE_CHECKING:
    from app.db.models.world import World
    from app.db.models.user import User


class Manuscript(Base):
    """Agrupador de resumos de sessões e contos (livro/diário)."""

    __tablename__ = "manuscripts"

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
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relacionamentos
    world: Mapped[World] = relationship(
        "World",
        back_populates="manuscripts",
    )
    creator: Mapped[User] = relationship(
        "User",
        back_populates="manuscripts",
    )
    chapters: Mapped[List[ManuscriptChapter]] = relationship(
        "ManuscriptChapter",
        back_populates="manuscript",
        cascade="all, delete-orphan",
        order_by="ManuscriptChapter.order_index",
    )

    def __repr__(self) -> str:
        return f"<Manuscript id={self.id} title={self.title!r}>"


class ManuscriptChapter(Base):
    """Capítulos/Momentos marcantes dentro de um manuscrito."""

    __tablename__ = "manuscript_chapters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("manuscripts.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    visibility: Mapped[VisibilityType] = mapped_column(
        Enum(VisibilityType, name="visibility_type", create_type=False),
        nullable=False,
        default=VisibilityType.NULA,
    )

    # Relacionamentos
    manuscript: Mapped[Manuscript] = relationship(
        "Manuscript",
        back_populates="chapters",
    )

    def __repr__(self) -> str:
        return f"<ManuscriptChapter id={self.id} title={self.title!r} visibility={self.visibility}>"
