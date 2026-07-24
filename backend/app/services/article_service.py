from __future__ import annotations

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.db.models.user import User
from app.db.models.article import Article, ArticleSection, ArticleTag, CharacterInventory
from app.db.models.enums import UserRole, VisibilityType
from app.core.fog_of_war import sanitize_article_dict
from app.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    CharacterInventoryCreate,
    CharacterInventoryResponse,
)


async def list_articles(
    db: AsyncSession,
    world_id: uuid.UUID,
    role: UserRole,
    tag: Optional[str] = None,
    search: Optional[str] = None,
) -> List[dict]:
    """Lista artigos de um mundo aplicando busca, filtro por tag e sanitização do Fog of War."""
    stmt = (
        select(Article)
        .options(
            selectinload(Article.sections),
            selectinload(Article.tags),
            selectinload(Article.inventory_items),
        )
        .where(Article.world_id == world_id)
    )

    if tag:
        stmt = stmt.join(Article.tags).where(ArticleTag.name == tag)

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(Article.title.ilike(pattern))

    stmt = stmt.order_by(Article.title.asc())
    res = await db.execute(stmt)
    articles = list(res.scalars().unique().all())

    sanitizer_list = []
    for art in articles:
        sanitized = sanitize_article_dict(art, role)
        if sanitized is not None:
            sanitizer_list.append(sanitized)

    return sanitizer_list


async def create_article(
    db: AsyncSession,
    world_id: uuid.UUID,
    user: User,
    role: UserRole,
    data: ArticleCreate,
) -> dict:
    """Cria um novo artigo respeitando os defaults de visibilidade RN-01 e RN-02."""
    # Regra de Default de Visibilidade
    visibility = data.visibility
    if visibility is None:
        if role == UserRole.MESTRE:
            visibility = VisibilityType.NULA  # RN-01
        else:
            visibility = VisibilityType.TOTAL  # RN-02

    article = Article(
        world_id=world_id,
        title=data.title,
        visibility=visibility,
        in_game_date=data.in_game_date,
        in_game_sort_order=data.in_game_sort_order,
        created_by=user.id,
    )
    db.add(article)
    await db.flush()

    # Adiciona seções
    for sec_data in data.sections:
        sec = ArticleSection(
            article_id=article.id,
            title=sec_data.title,
            content=sec_data.content,
            order_index=sec_data.order_index,
        )
        db.add(sec)

    # Adiciona tags
    for tag_name in data.tags:
        t = ArticleTag(
            article_id=article.id,
            name=tag_name,
        )
        db.add(t)

    await db.commit()

    # Recarrega relacionamentos
    stmt = (
        select(Article)
        .options(
            selectinload(Article.sections),
            selectinload(Article.tags),
            selectinload(Article.inventory_items),
        )
        .where(Article.id == article.id)
    )
    res = await db.execute(stmt)
    article_loaded = res.scalar_one()

    return sanitize_article_dict(article_loaded, role)


async def get_article_detail(
    db: AsyncSession,
    world_id: uuid.UUID,
    article_id: uuid.UUID,
    role: UserRole,
) -> dict:
    """Obtém os detalhes de um artigo específico com Fog of War."""
    stmt = (
        select(Article)
        .options(
            selectinload(Article.sections),
            selectinload(Article.tags),
            selectinload(Article.inventory_items),
        )
        .where(Article.id == article_id, Article.world_id == world_id)
    )
    res = await db.execute(stmt)
    article = res.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artigo não encontrado.",
        )

    sanitized = sanitize_article_dict(article, role)
    if sanitized is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artigo não encontrado.",
        )

    return sanitized


async def update_article(
    db: AsyncSession,
    world_id: uuid.UUID,
    article_id: uuid.UUID,
    user: User,
    role: UserRole,
    data: ArticleUpdate,
) -> dict:
    """Atualiza um artigo."""
    stmt = (
        select(Article)
        .options(
            selectinload(Article.sections),
            selectinload(Article.tags),
            selectinload(Article.inventory_items),
        )
        .where(Article.id == article_id, Article.world_id == world_id)
    )
    res = await db.execute(stmt)
    article = res.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artigo não encontrado.",
        )

    # Apenas Mestre ou Criador pode alterar
    if role != UserRole.MESTRE and article.created_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada para editar este artigo.",
        )

    if data.title is not None:
        article.title = data.title
    if data.visibility is not None and role == UserRole.MESTRE:
        article.visibility = data.visibility
    if data.in_game_date is not None:
        article.in_game_date = data.in_game_date
    if data.in_game_sort_order is not None:
        article.in_game_sort_order = data.in_game_sort_order

    if data.tags is not None:
        # Substitui tags existentes
        for t in article.tags:
            await db.delete(t)
        article.tags = [ArticleTag(article_id=article.id, name=name) for name in data.tags]

    if data.sections is not None:
        for sec in article.sections:
            await db.delete(sec)
        article.sections = [
            ArticleSection(
                article_id=article.id,
                title=s.title,
                content=s.content,
                order_index=s.order_index,
            )
            for s in data.sections
        ]

    await db.commit()
    await db.refresh(article)
    return sanitize_article_dict(article, role)


async def delete_article(
    db: AsyncSession,
    world_id: uuid.UUID,
    article_id: uuid.UUID,
    user: User,
    role: UserRole,
) -> None:
    """Remove um artigo."""
    stmt = select(Article).where(Article.id == article_id, Article.world_id == world_id)
    res = await db.execute(stmt)
    article = res.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artigo não encontrado.",
        )

    if role != UserRole.MESTRE and article.created_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada para deletar este artigo.",
        )

    await db.delete(article)
    await db.commit()


async def add_inventory_item(
    db: AsyncSession,
    world_id: uuid.UUID,
    article_id: uuid.UUID,
    data: CharacterInventoryCreate,
) -> CharacterInventoryResponse:
    """Adiciona item ao inventário de um artigo de personagem."""
    stmt = select(Article).where(Article.id == article_id, Article.world_id == world_id)
    res = await db.execute(stmt)
    article = res.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artigo não encontrado.",
        )

    item = CharacterInventory(
        article_id=article_id,
        item_name=data.item_name,
        quantity=data.quantity,
        description=data.description,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return CharacterInventoryResponse.model_validate(item)
