from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    String,
    Text,
    DateTime,
    BigInteger,
    Integer,
    ForeignKey,
    Enum,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.models.enums import VisibilityType

if TYPE_CHECKING:
    from app.db.models.world import World
    from app.db.models.user import User
    from app.db.models.map import MapPin


class Article(Base):
    """Entidade central da enciclopédia/codex (lore)."""

    __tablename__ = "articles"
    __table_args__ = (
        Index("idx_articles_world_visibility", "world_id", "visibility"),
        Index(
            "idx_articles_timeline",
            "world_id",
            "in_game_sort_order",
            postgresql_where=mapped_column("in_game_sort_order").isnot(None),
        ),
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
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    visibility: Mapped[VisibilityType] = mapped_column(
        Enum(VisibilityType, name="visibility_type", create_type=False),
        nullable=False,
        default=VisibilityType.NULA,
    )
    in_game_date: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    in_game_sort_order: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relacionamentos
    world: Mapped[World] = relationship(
        "World",
        back_populates="articles",
    )
    creator: Mapped[User] = relationship(
        "User",
        back_populates="articles",
    )
    sections: Mapped[List[ArticleSection]] = relationship(
        "ArticleSection",
        back_populates="article",
        cascade="all, delete-orphan",
        order_by="ArticleSection.order_index",
    )
    tags: Mapped[List[ArticleTag]] = relationship(
        "ArticleTag",
        back_populates="article",
        cascade="all, delete-orphan",
    )
    inventory_items: Mapped[List[CharacterInventory]] = relationship(
        "CharacterInventory",
        back_populates="article",
        cascade="all, delete-orphan",
    )
    targeted_by_pins: Mapped[List[MapPin]] = relationship(
        "MapPin",
        back_populates="target_article",
        foreign_keys="MapPin.target_article_id",
    )

    def __repr__(self) -> str:
        return f"<Article id={self.id} title={self.title!r} visibility={self.visibility}>"


class ArticleSection(Base):
    """Bloco organizacional de conteúdo dentro de um artigo."""

    __tablename__ = "article_sections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
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

    # Relacionamentos
    article: Mapped[Article] = relationship(
        "Article",
        back_populates="sections",
    )

    def __repr__(self) -> str:
        return f"<ArticleSection id={self.id} title={self.title!r} order={self.order_index}>"


class ArticleTag(Base):
    """Etiqueta para categorização e filtragem avançada de artigos."""

    __tablename__ = "article_tags"
    __table_args__ = (
        Index("idx_article_tags_name", "name"),
        Index("idx_article_tags_article", "article_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Relacionamentos
    article: Mapped[Article] = relationship(
        "Article",
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<ArticleTag id={self.id} name={self.name!r}>"


class CharacterInventory(Base):
    """Item de mochila/inventário vinculado a um artigo de personagem."""

    __tablename__ = "character_inventories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relacionamentos
    article: Mapped[Article] = relationship(
        "Article",
        back_populates="inventory_items",
    )

    def __repr__(self) -> str:
        return f"<CharacterInventory id={self.id} item={self.item_name!r} qty={self.quantity}>"
