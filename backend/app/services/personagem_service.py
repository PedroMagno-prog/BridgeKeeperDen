"""
Serviço assíncrono de Personagem.

Contém a lógica de negócio separada da camada de roteamento (API),
incluindo a validação do limite de 5 personagens por usuário.
"""
from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.personagem import Personagem

# Limite máximo de personagens por usuário
LIMITE_PERSONAGENS = 5


class LimitePersonagensError(Exception):
    """Lançada quando o usuário já atingiu o máximo de personagens."""


async def contar_personagens(db: AsyncSession, jogador_id: int) -> int:
    """Retorna quantos personagens o usuário já possui."""
    resultado = await db.execute(
        select(func.count()).where(Personagem.jogador_id == jogador_id)
    )
    return resultado.scalar_one()


async def criar_personagem(
    db: AsyncSession,
    jogador_id: int,
    nome: str,
    classe: str,
    raca: str,
) -> Personagem:
    """
    Cria e persiste um novo Personagem para o usuário.

    Raises:
        LimitePersonagensError: se o usuário já tiver 5 personagens.
    """
    total = await contar_personagens(db, jogador_id)

    if total >= LIMITE_PERSONAGENS:
        raise LimitePersonagensError(
            f"Usuário id={jogador_id} já possui {LIMITE_PERSONAGENS} personagens "
            "(limite máximo atingido)."
        )

    personagem = Personagem(
        nome=nome,
        classe=classe,
        raca=raca,
        jogador_id=jogador_id,
    )
    db.add(personagem)
    await db.flush()   # garante que o id seja preenchido antes do commit
    return personagem


async def listar_personagens(db: AsyncSession, jogador_id: int) -> list[Personagem]:
    """Retorna todos os personagens de um usuário."""
    resultado = await db.execute(
        select(Personagem).where(Personagem.jogador_id == jogador_id)
    )
    return list(resultado.scalars().all())


async def deletar_personagem(
    db: AsyncSession, personagem_id: int, jogador_id: int
) -> bool:
    """
    Remove um personagem pelo id.

    Verifica que o personagem pertence ao jogador antes de deletar.
    Retorna True se deletado, False se não encontrado.
    """
    resultado = await db.execute(
        select(Personagem).where(
            Personagem.id == personagem_id,
            Personagem.jogador_id == jogador_id,
        )
    )
    personagem = resultado.scalar_one_or_none()

    if not personagem:
        return False

    await db.delete(personagem)
    return True
