"""Model de seção de artigo (tabela `article_sections`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class ArticleSection(Base):
    """Bloco organizacional dentro de um artigo (título + conteúdo)."""

    __tablename__ = "article_sections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="",
        comment="Conteúdo da seção — suporta Markdown e @Mentions",
    )
    order_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    article: Mapped["Article"] = relationship("Article", back_populates="sections")

    def __repr__(self) -> str:
        return f"<ArticleSection id={self.id} title={self.title!r}>"
