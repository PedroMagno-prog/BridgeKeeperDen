from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.world import World


class TimelineEra(Base):
    """Divisores e eras históricas para agrupar visualmente eventos da Linha do Tempo."""

    __tablename__ = "timeline_eras"

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
        String(100),
        nullable=False,
    )
    start_sort_order: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    end_sort_order: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    # Relacionamentos
    world: Mapped[World] = relationship(
        "World",
        back_populates="timeline_eras",
    )

    def __repr__(self) -> str:
        return f"<TimelineEra id={self.id} title={self.title!r} range=({self.start_sort_order}..{self.end_sort_order})>"
