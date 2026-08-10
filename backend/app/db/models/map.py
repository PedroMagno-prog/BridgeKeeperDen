"""Model de mapa (tabela `maps`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db.session import Base


class Map(Base):
    """Imagem de mapa interativo de um mundo."""

    __tablename__ = "maps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    image_url: Mapped[str] = mapped_column(
        String(500), nullable=False,
        comment="Caminho do arquivo de imagem otimizado (WebP/JPG)",
    )
    created_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    world: Mapped["World"] = relationship("World", back_populates="maps")
    layers: Mapped[list["MapLayer"]] = relationship(
        "MapLayer",
        back_populates="map",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    pins: Mapped[list["MapPin"]] = relationship(
        "MapPin",
        back_populates="map",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="MapPin.map_id",
    )

    def __repr__(self) -> str:
        return f"<Map id={self.id} title={self.title!r}>"
