"""Model de artigo/codex (tabela `articles`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, BigInteger, ForeignKey, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db.session import Base
from app.db.models.enums import VisibilityType


class Article(Base):
    """Entidade central da enciclopédia/codex de um mundo."""

    __tablename__ = "articles"
    __table_args__ = (
        Index("idx_articles_world_visibility", "world_id", "visibility"),
        Index(
            "idx_articles_timeline",
            "world_id",
            "in_game_sort_order",
            postgresql_where="in_game_sort_order IS NOT NULL",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    visibility: Mapped[VisibilityType] = mapped_column(
        Enum(VisibilityType, name="visibility_type", create_constraint=False, native_enum=True),
        nullable=False,
        default=VisibilityType.NULA,
    )
    in_game_date: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Data fictícia do mundo (ex: '1442 D.C.')",
    )
    in_game_sort_order: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="Inteiro normalizado para ordenação na Timeline",
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    world: Mapped["World"] = relationship("World", back_populates="articles")
    creator: Mapped["User"] = relationship("User", lazy="selectin")
    sections: Mapped[list["ArticleSection"]] = relationship(
        "ArticleSection",
        back_populates="article",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ArticleSection.order_index",
    )
    tags: Mapped[list["ArticleTag"]] = relationship(
        "ArticleTag",
        back_populates="article",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    inventory_items: Mapped[list["CharacterInventory"]] = relationship(
        "CharacterInventory",
        back_populates="article",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Article id={self.id} title={self.title!r}>"
