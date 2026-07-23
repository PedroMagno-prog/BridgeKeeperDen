from __future__ import annotations

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Personagem(Base):
    """Modelo de personagem vinculado a um Usuario."""

    __tablename__ = "personagens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    classe: Mapped[str] = mapped_column(String(100), nullable=False)
    raca: Mapped[str] = mapped_column(String(100), nullable=False)

    # Chave estrangeira para Usuario
    jogador_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relacionamento N-1 com Usuario
    jogador: Mapped["Usuario"] = relationship(
        "Usuario",
        back_populates="personagens",
    )

    def __repr__(self) -> str:
        return f"<Personagem id={self.id} nome={self.nome!r} classe={self.classe!r}>"
