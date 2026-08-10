"""Model de manuscrito/diário de sessão (tabela `manuscripts`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db.session import Base


class Manuscript(Base):
    """Agrupador de resumos de sessões e contos."""

    __tablename__ = "manuscripts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    world: Mapped["World"] = relationship("World", back_populates="manuscripts")
    creator: Mapped["User"] = relationship("User", lazy="selectin")
    chapters: Mapped[list["ManuscriptChapter"]] = relationship(
        "ManuscriptChapter",
        back_populates="manuscript",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ManuscriptChapter.order_index",
    )

    def __repr__(self) -> str:
        return f"<Manuscript id={self.id} title={self.title!r}>"
