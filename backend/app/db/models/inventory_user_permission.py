"""Model de permissão granular por usuário para Inventários."""
from __future__ import annotations

import uuid
from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base
from app.db.models.enums import VisibilityType


class InventoryUserPermission(Base):
    """Permissão de acesso atribuída a um usuário individual em um inventário."""

    __tablename__ = "inventory_user_permissions"
    __table_args__ = (
        UniqueConstraint("inventory_id", "user_id", name="uq_inventory_user_perm"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    inventory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventories.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    visibility: Mapped[VisibilityType] = mapped_column(
        Enum(VisibilityType, native_enum=True, name="visibility_type", create_type=False),
        nullable=False,
    )
