"""Model de Item de Inventário (tabela `inventory_items`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db.session import Base


class InventoryItem(Base):
    """Slot/Item contido dentro de um inventário, opcionalmente vinculado a um Artigo (Lore/Codex)."""

    __tablename__ = "inventory_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    inventory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventories.id", ondelete="CASCADE"),
        nullable=False,
    )
    article_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="SET NULL"),
        nullable=True,
    )
    custom_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Sobrescrita/Nome customizado do item"
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Anotações e cargas específicas")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    inventory: Mapped["Inventory"] = relationship("Inventory", back_populates="items")
    article: Mapped["Article | None"] = relationship("Article", lazy="selectin")

    def __repr__(self) -> str:
        return f"<InventoryItem id={self.id} custom_name={self.custom_name!r}>"
