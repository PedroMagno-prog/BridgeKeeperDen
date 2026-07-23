from __future__ import annotations

from sqlalchemy import String, ForeignKey, CheckConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy.exc import ValueError as SAValueError

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


# ── Validação do limite de 5 personagens por usuário ─────────────────────────

def _validar_limite_personagens(mapper, connection, target: Personagem) -> None:
    """
    Evento SQLAlchemy 'before_insert' que impede um usuário de ter mais de 5
    personagens. Executado antes de cada INSERT na tabela 'personagens'.
    """
    from sqlalchemy import select, func
    from app.db.models.usuario import Usuario

    count = connection.execute(
        select(func.count()).where(Personagem.jogador_id == target.jogador_id)
    ).scalar_one()

    if count >= 5:
        raise ValueError(
            f"Usuário id={target.jogador_id} já possui 5 personagens (limite máximo)."
        )


event.listen(Personagem, "before_insert", _validar_limite_personagens)
