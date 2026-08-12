"""Model de Inventário (tabela `inventories`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, Text, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db.session import Base
from app.db.models.enums import VisibilityType


class Inventory(Base):
    """Inventário individual (ex: Armaria do Ferreiro, Mochila do Personagem X)."""

    __tablename__ = "inventories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
    )
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    owner_article_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    limit: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Capacidade de itens/slots (aviso não-bloqueante)"
    )
    visibility: Mapped[VisibilityType] = mapped_column(
        Enum(VisibilityType, name="visibility_type", create_constraint=False, native_enum=True),
        nullable=False,
        default=VisibilityType.NULA,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    world: Mapped["World"] = relationship("World")
    group: Mapped["InventoryGroup | None"] = relationship("InventoryGroup", back_populates="inventories")
    owner_article: Mapped["Article | None"] = relationship("Article", foreign_keys=[owner_article_id])
    creator: Mapped["User"] = relationship("User", lazy="selectin")
    items: Mapped[list["InventoryItem"]] = relationship(
        "InventoryItem",
        back_populates="inventory",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="InventoryItem.order_index",
    )

    def __repr__(self) -> str:
        return f"<Inventory id={self.id} name={self.name!r}>"
