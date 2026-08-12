"""Model de Grupo de Inventário (tabela `inventory_groups`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db.session import Base
from app.db.models.enums import VisibilityType


class InventoryGroup(Base):
    """Grupo organizacional para inventários (ex: Lojas de uma Cidade, Mochilas do Grupo)."""

    __tablename__ = "inventory_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[VisibilityType] = mapped_column(
        Enum(VisibilityType, name="visibility_type", create_constraint=False, native_enum=True),
        nullable=False,
        default=VisibilityType.NULA,
    )
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True, default="folder")
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
    creator: Mapped["User"] = relationship("User", lazy="selectin")
    inventories: Mapped[list["Inventory"]] = relationship(
        "Inventory",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<InventoryGroup id={self.id} name={self.name!r}>"
