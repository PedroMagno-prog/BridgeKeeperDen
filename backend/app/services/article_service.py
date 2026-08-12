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
    populate_existing: bool = False,
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
    if populate_existing:
        stmt = stmt.execution_options(populate_existing=True)
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

    # Replace tags — deleta via ORM para remover da identity map, depois insere novos
    if tags is not None:
        for tag in list(article.tags):
            await db.delete(tag)
        await db.flush()
        for tag_name in tags:
            db.add(ArticleTag(article_id=article.id, name=tag_name))

    # Replace sections — mesma estrategia
    if sections is not None:
        for section in list(article.sections):
            await db.delete(section)
        await db.flush()
        for sec_data in sections:
            db.add(ArticleSection(
                article_id=article.id,
                title=sec_data["title"],
                content=sec_data.get("content", ""),
                order_index=sec_data.get("order_index", 0),
            ))

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
    await db.flush()
    return new_items


# ── Wikilinks, Autocomplete & Backlinks ───────────────────────────────────────

import re

WIKILINK_REGEX = re.compile(r"\[\[([^\]\|]+)(?:\|([^\]]+))?\]\]")


def extract_wikilinks(content: str) -> list[tuple[str, str | None]]:
    """
    Extrai todas as citações [[Artigo]] ou [[Artigo|Rótulo]] de um texto.
    Retorna lista de tuplas (target_title, display_text).
    """
    if not content:
        return []
    matches = WIKILINK_REGEX.findall(content)
    return [(m[0].strip(), m[1].strip() if m[1] else None) for m in matches if m[0].strip()]


async def resolver_artigo_por_titulo(
    db: AsyncSession,
    world_id: uuid.UUID,
    title: str,
    role: UserRole,
) -> dict:
    """
    Busca um artigo pelo título exato (case-insensitive).
    Respeita a Névoa de Guerra (Fog of War).
    """
    stmt = (
        select(Article)
        .where(Article.world_id == world_id, Article.title.ilike(title.strip()))
    )
    result = await db.execute(stmt)
    article = result.scalars().first()

    if not article:
        return {
            "exists": False,
            "article_id": None,
            "title": title.strip(),
            "visibility": None,
            "is_locked": False,
        }

    # Fog of War check
    if role == UserRole.JOGADOR and article.visibility == VisibilityType.NULA:
        return {
            "exists": False,
            "article_id": None,
            "title": title.strip(),
            "visibility": None,
            "is_locked": False,
        }

    is_locked = role == UserRole.JOGADOR and article.visibility == VisibilityType.PARCIAL
    return {
        "exists": True,
        "article_id": article.id,
        "title": article.title,
        "visibility": article.visibility,
        "is_locked": is_locked,
    }


async def buscar_mencao_sugestoes(
    db: AsyncSession,
    world_id: uuid.UUID,
    query: str,
    role: UserRole,
    limit: int = 10,
) -> list[Article]:
    """
    Busca artigos por título (autocomplete) para menções/wikilinks.
    Filtra Névoa de Guerra NULA para jogadores.
    """
    stmt = (
        select(Article)
        .options(selectinload(Article.tags))
        .where(Article.world_id == world_id)
    )

    if role == UserRole.JOGADOR:
        stmt = stmt.where(Article.visibility != VisibilityType.NULA)

    if query.strip():
        stmt = stmt.where(Article.title.ilike(f"%{query.strip()}%"))

    stmt = stmt.order_by(Article.title.asc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def buscar_backlinks(
    db: AsyncSession,
    world_id: uuid.UUID,
    article_id: uuid.UUID,
    role: UserRole,
) -> list[dict]:
    """
    Busca todas as seções de artigos no mundo que mencionam o título do artigo atual.
    Retorna lista de referências (backlinks) sanitizadas respeitando a Névoa de Guerra.
    """
    # 1. Obter o artigo alvo para saber o seu título
    target_article = await buscar_artigo(db, article_id, world_id)
    if not target_article:
        return []

    target_title = target_article.title.lower()

    # 2. Buscar seções de artigos do mesmo mundo (excluindo o próprio artigo)
    stmt = (
        select(ArticleSection, Article)
        .join(Article, ArticleSection.article_id == Article.id)
        .where(Article.world_id == world_id, Article.id != article_id)
    )

    if role == UserRole.JOGADOR:
        stmt = stmt.where(Article.visibility != VisibilityType.NULA)

    result = await db.execute(stmt)
    rows = result.all()

    backlinks = []
    for section, source_article in rows:
        content_lower = section.content.lower()
        if f"[[{target_title}" in content_lower:
            is_locked = role == UserRole.JOGADOR and source_article.visibility == VisibilityType.PARCIAL

            # Extrai um pequeno trecho (snippet)
            idx = content_lower.find(f"[[{target_title}")
            start = max(0, idx - 40)
            end = min(len(section.content), idx + len(target_title) + 50)
            snippet = ("..." if start > 0 else "") + section.content[start:end] + ("..." if end < len(section.content) else "")

            backlinks.append({
                "article_id": source_article.id,
                "title": source_article.title,
                "visibility": source_article.visibility,
                "section_title": section.title,
                "snippet": snippet if not is_locked else "Conteúdo protegido por Névoa de Guerra Parcial.",
                "is_locked": is_locked,
            })

    return backlinks
