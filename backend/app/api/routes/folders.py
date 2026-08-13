"""Rotas da API para gerenciamento de Pastas (ArticleFolder) e Árvore do Codex."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.world_access import WorldContext, get_world_ctx
from app.schemas.folder import (
    FolderCreate,
    FolderResponse,
    FolderUpdate,
    WorldFolderTreeResponse,
)
from app.services import folder_service

router = APIRouter()


@router.get(
    "/",
    response_model=WorldFolderTreeResponse,
    summary="Obtém a árvore hierárquica completa de pastas e artigos do mundo",
)
async def obter_arvore_pastas(
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """
    Retorna a árvore hierárquica de pastas e os artigos contidos em cada pasta (e na raiz do mundo).
    Respeita a Névoa de Guerra (Fog of War) para o papel de usuário atual.
    """
    return await folder_service.obter_arvore_pastas_do_mundo(
        db, ctx.world_id, ctx.role, ctx.user.id
    )


@router.post(
    "/",
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova pasta de artigos",
)
async def criar_pasta(
    body: FolderCreate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Cria uma nova pasta no mundo ativo."""
    folder = await folder_service.criar_pasta(db, ctx.world_id, body)
    await db.commit()
    await db.refresh(folder)
    return folder


@router.put(
    "/{folder_id}",
    response_model=FolderResponse,
    summary="Atualiza ou move uma pasta de artigos",
)
async def atualizar_pasta(
    folder_id: int,
    body: FolderUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Atualiza o nome ou a pasta pai (parent_id) de uma pasta existente."""
    folder = await folder_service.atualizar_pasta(db, folder_id, ctx.world_id, body)
    await db.commit()
    await db.refresh(folder)
    return folder


@router.delete(
    "/{folder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui uma pasta de artigos",
)
async def deletar_pasta(
    folder_id: int,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Exclui uma pasta. Artigos associados terão seu folder_id definido para NULL."""
    await folder_service.deletar_pasta(db, folder_id, ctx.world_id)
    await db.commit()
