"""Model de tag de artigo (tabela `article_tags`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class ArticleTag(Base):
    """Etiqueta para categorização e busca avançada de artigos."""

    __tablename__ = "article_tags"
    __table_args__ = (
        Index("idx_article_tags_name", "name"),
        Index("idx_article_tags_article", "article_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Nome da tag (ex: .Hostil, .NPC, .Facção)",
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    article: Mapped["Article"] = relationship("Article", back_populates="tags")

    def __repr__(self) -> str:
        return f"<ArticleTag id={self.id} name={self.name!r}>"
