from __future__ import annotations

from sqlalchemy import String, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Usuario(Base):
    """Modelo de usuário da aplicação."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha: Mapped[str] = mapped_column(String(255), nullable=False, comment="Hash bcrypt da senha")

    # Relacionamento 1-N com Personagem
    personagens: Mapped[list["Personagem"]] = relationship(
        "Personagem",
        back_populates="jogador",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} email={self.email!r}>"
