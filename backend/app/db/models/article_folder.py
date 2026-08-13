"""Model de Pasta de Artigos (tabela `article_folders`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db.session import Base


class ArticleFolder(Base):
    """Pasta organizacional hierárquica para artigos do mundo."""

    __tablename__ = "article_folders"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("article_folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    world: Mapped["World"] = relationship("World")
    parent: Mapped["ArticleFolder | None"] = relationship(
        "ArticleFolder",
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[list["ArticleFolder"]] = relationship(
        "ArticleFolder",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    articles: Mapped[list["Article"]] = relationship(
        "Article",
        back_populates="folder",
    )

    def __repr__(self) -> str:
        return f"<ArticleFolder id={self.id} name={self.name!r}>"
