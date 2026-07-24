"""Model de camada de mapa (tabela `map_layers`)."""
from __future__ import annotations

import uuid

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class MapLayer(Base):
    """Camada organizacional de marcadores em um mapa."""

    __tablename__ = "map_layers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    map_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("maps.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Nome da camada (ex: 'Cidades', 'Rotas de Comércio')",
    )
    is_default_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Se a camada vem visível por padrão",
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    map: Mapped["Map"] = relationship("Map", back_populates="layers")

    def __repr__(self) -> str:
        return f"<MapLayer id={self.id} name={self.name!r}>"
