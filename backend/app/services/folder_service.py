"""Serviço assíncrono para manipulação e montagem da árvore hierárquica de pastas (ArticleFolder)."""
from __future__ import annotations

import uuid
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.article import Article
from app.db.models.article_folder import ArticleFolder
from app.db.models.enums import UserRole, VisibilityType
from app.schemas.folder import (
    ArticleSummarySchema,
    FolderCreate,
    FolderTreeResponse,
    FolderUpdate,
    WorldFolderTreeResponse,
)
from app.services.fog_of_war import resolve_effective_visibility, sanitize_article_for_list


async def criar_pasta(
    db: AsyncSession,
    world_id: uuid.UUID,
    data: FolderCreate,
) -> ArticleFolder:
    """
    Cria uma nova pasta de artigos garantindo que parent_id pertença ao mesmo mundo.
    """
    if data.parent_id is not None:
        parent_res = await db.execute(
            select(ArticleFolder).where(
                ArticleFolder.id == data.parent_id,
                ArticleFolder.world_id == world_id,
            )
        )
        parent_folder = parent_res.scalar_one_or_none()
        if not parent_folder:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A pasta pai especificada não existe neste mundo.",
            )

    folder = ArticleFolder(
        world_id=world_id,
        name=data.name.strip(),
        parent_id=data.parent_id,
    )
    db.add(folder)
    await db.flush()
    return folder


async def atualizar_pasta(
    db: AsyncSession,
    folder_id: int,
    world_id: uuid.UUID,
    data: FolderUpdate,
) -> ArticleFolder:
    """
    Atualiza nome e/ou move a pasta para outro parent_id (prevenindo ciclos).
    """
    res = await db.execute(
        select(ArticleFolder).where(
            ArticleFolder.id == folder_id,
            ArticleFolder.world_id == world_id,
        )
    )
    folder = res.scalar_one_or_none()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pasta não encontrada.",
        )

    if data.parent_id is not None:
        if data.parent_id == folder_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uma pasta não pode ser sua própria pasta pai.",
            )

        # Validar pertencimento da pasta pai
        parent_res = await db.execute(
            select(ArticleFolder).where(
                ArticleFolder.id == data.parent_id,
                ArticleFolder.world_id == world_id,
            )
        )
        parent_folder = parent_res.scalar_one_or_none()
        if not parent_folder:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A pasta pai especificada não existe neste mundo.",
            )

    if data.name is not None:
        folder.name = data.name.strip()

    if data.parent_id is not ...:
        folder.parent_id = data.parent_id

    await db.flush()
    return folder


async def deletar_pasta(
    db: AsyncSession,
    folder_id: int,
    world_id: uuid.UUID,
) -> None:
    """
    Exclui uma pasta de artigos do mundo.
    """
    res = await db.execute(
        select(ArticleFolder).where(
            ArticleFolder.id == folder_id,
            ArticleFolder.world_id == world_id,
        )
    )
    folder = res.scalar_one_or_none()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pasta não encontrada.",
        )

    await db.delete(folder)
    await db.flush()


async def obter_arvore_pastas_do_mundo(
    db: AsyncSession,
    world_id: uuid.UUID,
    role: UserRole,
    user_id: uuid.UUID,
) -> WorldFolderTreeResponse:
    """
    Busca todas as pastas e artigos do mundo e constrói a árvore hierárquica em memória.
    Respeita a Névoa de Guerra (Fog of War) e permissões de visibilidade.
    """
    # 1. Buscar todas as pastas do mundo
    folders_res = await db.execute(
        select(ArticleFolder)
        .where(ArticleFolder.world_id == world_id)
        .order_by(ArticleFolder.name.asc())
    )
    all_folders = folders_res.scalars().all()

    # 2. Buscar todos os artigos do mundo
    stmt_art = (
        select(Article)
        .options(selectinload(Article.tags))
        .where(Article.world_id == world_id)
    )
    if role == UserRole.JOGADOR:
        stmt_art = stmt_art.where(Article.visibility != VisibilityType.NULA)
    stmt_art = stmt_art.order_by(Article.title.asc())

    art_res = await db.execute(stmt_art)
    all_articles = art_res.scalars().all()

    # Buscar permissões específicas do usuário
    from app.db.models.article_user_permission import ArticleUserPermission
    perm_res = await db.execute(
        select(ArticleUserPermission.article_id, ArticleUserPermission.visibility).where(
            ArticleUserPermission.user_id == user_id
        )
    )
    user_perms = {row[0]: row[1] for row in perm_res.all()}

    # 3. Sanitizar artigos e agrupar por folder_id
    articles_by_folder: dict[int | None, list[ArticleSummarySchema]] = {}
    for art in all_articles:
        spec_perm = user_perms.get(art.id)
        sanitized = sanitize_article_for_list(art, role, user_id, spec_perm)
        if sanitized is None:
            continue

        summary = ArticleSummarySchema(**sanitized)
        folder_key = art.folder_id
        articles_by_folder.setdefault(folder_key, []).append(summary)

    # 4. Agrupar pastas por parent_id
    folders_by_parent: dict[int | None, list[ArticleFolder]] = {}
    for f in all_folders:
        folders_by_parent.setdefault(f.parent_id, []).append(f)

    # 5. Construir recursivamente o nó da árvore
    def build_tree_node(folder: ArticleFolder) -> FolderTreeResponse:
        child_folders = folders_by_parent.get(folder.id, [])
        children_nodes = [build_tree_node(cf) for cf in child_folders]
        folder_articles = articles_by_folder.get(folder.id, [])

        return FolderTreeResponse(
            id=folder.id,
            name=folder.name,
            parent_id=folder.parent_id,
            children=children_nodes,
            articles=folder_articles,
        )

    # Pastas raiz (parent_id == None)
    root_folders = folders_by_parent.get(None, [])
    root_folder_nodes = [build_tree_node(rf) for rf in root_folders]

    # Artigos na raiz (folder_id == None)
    root_articles = articles_by_folder.get(None, [])

    return WorldFolderTreeResponse(
        folders=root_folder_nodes,
        root_articles=root_articles,
    )
