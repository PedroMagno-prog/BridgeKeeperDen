"""
Servico assincrono de Article.

Contem a logica de negocio para CRUD de artigos, secoes, tags e inventario.
Aplica as regras RN-01 (default NULA para Mestre) e RN-02 (default TOTAL para Jogador).
"""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.article import Article
from app.db.models.article_section import ArticleSection
from app.db.models.article_tag import ArticleTag
from app.db.models.character_inventory import CharacterInventory
from app.db.models.enums import UserRole, VisibilityType


async def criar_artigo(
    db: AsyncSession,
    world_id: uuid.UUID,
    created_by: uuid.UUID,
    role: UserRole,
    *,
    title: str,
    visibility: VisibilityType | None,
    in_game_date: str | None,
    in_game_sort_order: int | None,
    tags: list[str],
    sections: list[dict],
) -> Article:
    """
    Cria um artigo com sections e tags em cascata.
    Aplica RN-01/RN-02 se visibility nao for informado.
    """
    # RN-01: Mestre -> NULA por default; RN-02: Jogador -> TOTAL por default
    if visibility is None:
        visibility = VisibilityType.NULA if role == UserRole.MESTRE else VisibilityType.TOTAL

    article = Article(
        world_id=world_id,
        title=title,
        visibility=visibility,
        in_game_date=in_game_date,
        in_game_sort_order=in_game_sort_order,
        created_by=created_by,
    )
    db.add(article)
    await db.flush()

    # Sections
    for sec_data in sections:
        section = ArticleSection(
            article_id=article.id,
            title=sec_data["title"],
            content=sec_data.get("content", ""),
            order_index=sec_data.get("order_index", 0),
        )
        db.add(section)

    # Tags
    for tag_name in tags:
        tag = ArticleTag(article_id=article.id, name=tag_name)
        db.add(tag)

    await db.flush()
    return article


async def listar_artigos(
    db: AsyncSession,
    world_id: uuid.UUID,
    role: UserRole,
    *,
    tag_filter: str | None = None,
    search: str | None = None,
) -> Sequence[Article]:
    """
    Lista artigos do mundo.
    JOGADOR: filtra NULA no nivel de query (RNF-03).
    """
    stmt = (
        select(Article)
        .options(selectinload(Article.tags))
        .where(Article.world_id == world_id)
    )

    # Fog of War: JOGADOR nunca ve artigos NULA
    if role == UserRole.JOGADOR:
        stmt = stmt.where(Article.visibility != VisibilityType.NULA)

    # Filtro por tag
    if tag_filter:
        stmt = stmt.where(
            Article.id.in_(
                select(ArticleTag.article_id).where(ArticleTag.name == tag_filter)
            )
        )

    # Busca textual
    if search:
        stmt = stmt.where(Article.title.ilike(f"%{search}%"))

    stmt = stmt.order_by(Article.updated_at.desc())

    result = await db.execute(stmt)
    return result.scalars().all()


async def buscar_artigo(
    db: AsyncSession,
    article_id: uuid.UUID,
    world_id: uuid.UUID,
) -> Article | None:
    """Busca um artigo com sections, tags e inventory carregados."""
    stmt = (
        select(Article)
        .options(
            selectinload(Article.sections),
            selectinload(Article.tags),
            selectinload(Article.inventory_items),
        )
        .where(Article.id == article_id, Article.world_id == world_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def atualizar_artigo(
    db: AsyncSession,
    article: Article,
    *,
    title: str | None = None,
    visibility: VisibilityType | None = None,
    in_game_date: str | None = ...,
    in_game_sort_order: int | None = ...,
    tags: list[str] | None = None,
    sections: list[dict] | None = None,
) -> Article:
    """
    Atualiza um artigo. Para tags e sections usa estrategia delete-and-recreate.
    """
    if title is not None:
        article.title = title
    if visibility is not None:
        article.visibility = visibility
    if in_game_date is not ...:
        article.in_game_date = in_game_date
    if in_game_sort_order is not ...:
        article.in_game_sort_order = in_game_sort_order

    # Replace tags — usa ORM-level delete para manter a identity map sincronizada
    if tags is not None:
        for tag in list(article.tags):
            await db.delete(tag)
        await db.flush()
        article.tags.clear()
        for tag_name in tags:
            new_tag = ArticleTag(article_id=article.id, name=tag_name)
            db.add(new_tag)
            article.tags.append(new_tag)

    # Replace sections — mesma estrategia
    if sections is not None:
        for section in list(article.sections):
            await db.delete(section)
        await db.flush()
        article.sections.clear()
        for sec_data in sections:
            new_sec = ArticleSection(
                article_id=article.id,
                title=sec_data["title"],
                content=sec_data.get("content", ""),
                order_index=sec_data.get("order_index", 0),
            )
            db.add(new_sec)
            article.sections.append(new_sec)

    await db.flush()
    return article


async def deletar_artigo(
    db: AsyncSession,
    article: Article,
) -> None:
    """Remove um artigo (CASCADE deleta sections, tags, inventory)."""
    await db.delete(article)


async def atualizar_inventario(
    db: AsyncSession,
    article_id: uuid.UUID,
    items: list[dict],
) -> list[CharacterInventory]:
    """Replace completo do inventario de um artigo."""
    await db.execute(
        delete(CharacterInventory).where(CharacterInventory.article_id == article_id)
    )

    new_items = []
    for item_data in items:
        item = CharacterInventory(
            article_id=article_id,
            item_name=item_data["item_name"],
            quantity=item_data.get("quantity", 1),
            description=item_data.get("description"),
        )
        db.add(item)
        new_items.append(item)

    await db.flush()
    return new_items
