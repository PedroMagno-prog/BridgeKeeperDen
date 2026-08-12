"""Model de permissão granular por usuário para Artigos."""
from __future__ import annotations

import uuid
from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base
from app.db.models.enums import VisibilityType


class ArticleUserPermission(Base):
    """Permissão de acesso atribuída a um usuário individual em um artigo."""

    __tablename__ = "article_user_permissions"
    __table_args__ = (
        UniqueConstraint("article_id", "user_id", name="uq_article_user_perm"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
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
