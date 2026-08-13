"""Model de marcador/pin de mapa (tabela `map_pins`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, Numeric, ForeignKey, Index, CheckConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base
from app.db.models.enums import VisibilityType


class MapPin(Base):
    """Marcador posicionado interativamente sobre a imagem do mapa."""

    __tablename__ = "map_pins"
    __table_args__ = (
        CheckConstraint("x_position BETWEEN 0 AND 100", name="ck_pin_x_range"),
        CheckConstraint("y_position BETWEEN 0 AND 100", name="ck_pin_y_range"),
        Index("idx_map_pins_map_visibility", "map_id", "visibility"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    map_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("maps.id", ondelete="CASCADE"),
        nullable=False,
    )
    layer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("map_layers.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_article_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="SET NULL"),
        nullable=True,
        comment="Link para artigo da wiki (opcional)",
    )
    target_map_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("maps.id", ondelete="SET NULL"),
        nullable=True,
        comment="Link para sub-mapa aninhado (opcional)",
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    x_position = mapped_column(
        Numeric(5, 2), nullable=False,
        comment="Coordenada X relativa em % (0 a 100)",
    )
    y_position = mapped_column(
        Numeric(5, 2), nullable=False,
        comment="Coordenada Y relativa em % (0 a 100)",
    )
    icon: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="default-pin",
    )
    color: Mapped[str] = mapped_column(
        String(7), nullable=False, server_default="#FF0000",
        comment="Código hexadecimal de cor",
    )
    visibility: Mapped[VisibilityType] = mapped_column(
        Enum(VisibilityType, name="visibility_type", create_constraint=False, native_enum=True),
        nullable=False,
        default=VisibilityType.NULA,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID do usuario criador do marcador",
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    map: Mapped["Map"] = relationship(
        "Map", back_populates="pins", foreign_keys=[map_id],
    )
    layer: Mapped["MapLayer | None"] = relationship("MapLayer", lazy="selectin")
    target_article: Mapped["Article | None"] = relationship("Article", lazy="selectin")
    target_map: Mapped["Map | None"] = relationship(
        "Map", foreign_keys=[target_map_id], lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<MapPin id={self.id} title={self.title!r} ({self.x_position},{self.y_position})>"
