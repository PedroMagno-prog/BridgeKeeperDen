"""Rotas de Personagem — CRUD completo."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.api.deps.database import get_db
from app.db.models.personagem import Personagem
from app.db.models.usuario import Usuario
from app.schemas.personagem import PersonagemCreate, PersonagemOut, PersonagemUpdate
from app.services import personagem_service
from app.services.personagem_service import LimitePersonagensError

router = APIRouter()


# ── helpers ───────────────────────────────────────────────────────────────────

async def _get_personagem_do_usuario(
    personagem_id: int,
    db: AsyncSession,
    usuario: Usuario,
) -> Personagem:
    """Busca personagem e garante que pertence ao usuário logado."""
    result = await db.execute(
        select(Personagem).where(
            Personagem.id == personagem_id,
            Personagem.jogador_id == usuario.id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personagem não encontrado.")
    return p


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[PersonagemOut], summary="Lista personagens do usuário")
async def listar(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return await personagem_service.listar_personagens(db, usuario.id)


@router.post(
    "/",
    response_model=PersonagemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo personagem",
)
async def criar(
    body: PersonagemCreate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    try:
        personagem = await personagem_service.criar_personagem(
            db, usuario.id, body.nome, body.classe, body.raca
        )
        await db.commit()
        await db.refresh(personagem)
        return personagem
    except LimitePersonagensError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/{personagem_id}", response_model=PersonagemOut, summary="Busca um personagem")
async def buscar(
    personagem_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return await _get_personagem_do_usuario(personagem_id, db, usuario)


@router.patch(
    "/{personagem_id}",
    response_model=PersonagemOut,
    summary="Atualiza parcialmente um personagem",
)
async def atualizar(
    personagem_id: int,
    body: PersonagemUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    personagem = await _get_personagem_do_usuario(personagem_id, db, usuario)

    data = body.model_dump(exclude_unset=True)
    for campo, valor in data.items():
        setattr(personagem, campo, valor)

    await db.commit()
    await db.refresh(personagem)
    return personagem


@router.delete(
    "/{personagem_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um personagem",
)
async def deletar(
    personagem_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    deletado = await personagem_service.deletar_personagem(db, personagem_id, usuario.id)
    if not deletado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personagem não encontrado.")
    await db.commit()
