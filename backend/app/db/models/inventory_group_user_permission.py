"""Model de permissão granular por usuário para Grupos de Inventário."""
from __future__ import annotations

import uuid
from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base
from app.db.models.enums import VisibilityType


class InventoryGroupUserPermission(Base):
    """Permissão de acesso atribuída a um usuário individual em um grupo de inventário."""

    __tablename__ = "inventory_group_user_permissions"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user_perm"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_groups.id", ondelete="CASCADE"),
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
