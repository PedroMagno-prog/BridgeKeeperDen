from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    String,
    DateTime,
    Boolean,
    Numeric,
    ForeignKey,
    Enum,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.models.enums import VisibilityType

if TYPE_CHECKING:
    from app.db.models.world import World
    from app.db.models.article import Article


class Map(Base):
    """Gerenciamento de imagens de mapa e cartografia interativa."""

    __tablename__ = "maps"

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
        String(100),
        nullable=False,
    )
    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relacionamentos
    world: Mapped[World] = relationship(
        "World",
        back_populates="maps",
    )
    layers: Mapped[List[MapLayer]] = relationship(
        "MapLayer",
        back_populates="map",
        cascade="all, delete-orphan",
    )
    pins: Mapped[List[MapPin]] = relationship(
        "MapPin",
        back_populates="map",
        cascade="all, delete-orphan",
        foreign_keys="MapPin.map_id",
    )
    targeted_by_pins: Mapped[List[MapPin]] = relationship(
        "MapPin",
        back_populates="target_map",
        foreign_keys="MapPin.target_map_id",
    )

    def __repr__(self) -> str:
        return f"<Map id={self.id} title={self.title!r}>"


class MapLayer(Base):
    """Camadas organizacionais de marcadores em um mapa."""

    __tablename__ = "map_layers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    map_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("maps.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    is_default_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Relacionamentos
    map: Mapped[Map] = relationship(
        "Map",
        back_populates="layers",
    )
    pins: Mapped[List[MapPin]] = relationship(
        "MapPin",
        back_populates="layer",
    )

    def __repr__(self) -> str:
        return f"<MapLayer id={self.id} name={self.name!r} active={self.is_default_active}>"


class MapPin(Base):
    """Marcador posicionado sobre a imagem do mapa."""

    __tablename__ = "map_pins"
    __table_args__ = (
        CheckConstraint("x_position >= 0 AND x_position <= 100", name="chk_x_position"),
        CheckConstraint("y_position >= 0 AND y_position <= 100", name="chk_y_position"),
        Index("idx_map_pins_map_visibility", "map_id", "visibility"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    map_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("maps.id", ondelete="CASCADE"),
        nullable=False,
    )
    layer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("map_layers.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_article_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_map_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("maps.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    x_position: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    y_position: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    icon: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="default-pin",
    )
    color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#FF0000",
    )
    visibility: Mapped[VisibilityType] = mapped_column(
        Enum(VisibilityType, name="visibility_type", create_type=False),
        nullable=False,
        default=VisibilityType.NULA,
    )

    # Relacionamentos
    map: Mapped[Map] = relationship(
        "Map",
        back_populates="pins",
        foreign_keys=[map_id],
    )
    layer: Mapped[Optional[MapLayer]] = relationship(
        "MapLayer",
        back_populates="pins",
    )
    target_article: Mapped[Optional[Article]] = relationship(
        "Article",
        back_populates="targeted_by_pins",
    )
    target_map: Mapped[Optional[Map]] = relationship(
        "Map",
        back_populates="targeted_by_pins",
        foreign_keys=[target_map_id],
    )

    def __repr__(self) -> str:
        return f"<MapPin id={self.id} title={self.title!r} pos=({self.x_position}, {self.y_position})>"
