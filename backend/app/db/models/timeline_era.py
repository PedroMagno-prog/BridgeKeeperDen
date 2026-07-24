"""Model de era histórica da timeline (tabela `timeline_eras`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class TimelineEra(Base):
    """Divisor/era histórica para agrupar visualmente eventos na timeline."""

    __tablename__ = "timeline_eras"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Nome da era (ex: 'Segunda Era da Magia')",
    )
    start_sort_order: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Valor de ordem inicial da era",
    )
    end_sort_order: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Valor de ordem final da era",
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    world: Mapped["World"] = relationship("World", back_populates="timeline_eras")

    def __repr__(self) -> str:
        return f"<TimelineEra id={self.id} title={self.title!r}>"
