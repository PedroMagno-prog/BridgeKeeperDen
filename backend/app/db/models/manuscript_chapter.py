"""Model de capítulo de manuscrito (tabela `manuscript_chapters`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, Text, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base
from app.db.models.enums import VisibilityType


class ManuscriptChapter(Base):
    """Capítulo/Momento marcante dentro de um manuscrito."""

    __tablename__ = "manuscript_chapters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("manuscripts.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="",
        comment="Texto do resumo — suporta Markdown e @Mentions",
    )
    order_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    visibility: Mapped[VisibilityType] = mapped_column(
        Enum(VisibilityType, name="visibility_type", create_constraint=False, native_enum=True),
        nullable=False,
        default=VisibilityType.NULA,
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    manuscript: Mapped["Manuscript"] = relationship("Manuscript", back_populates="chapters")

    def __repr__(self) -> str:
        return f"<ManuscriptChapter id={self.id} title={self.title!r}>"
