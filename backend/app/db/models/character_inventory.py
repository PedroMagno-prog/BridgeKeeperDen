"""Model de inventário de personagem (tabela `character_inventories`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class CharacterInventory(Base):
    """Item de mochila/inventário vinculado a artigos de personagens."""

    __tablename__ = "character_inventories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relacionamentos ───────────────────────────────────────────────────────
    article: Mapped["Article"] = relationship("Article", back_populates="inventory_items")

    def __repr__(self) -> str:
        return f"<CharacterInventory id={self.id} item={self.item_name!r}>"
