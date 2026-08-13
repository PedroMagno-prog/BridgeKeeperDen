"""
Servico assincrono de Article.

Contem a logica de negocio para CRUD de artigos, pastas, tags e inventario.
Aplica as regras RN-01 (default NULA para Mestre) e RN-02 (default TOTAL para Jogador).
"""
from __future__ import annotations

import re
import uuid
from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.article import Article
from app.db.models.article_folder import ArticleFolder
from app.db.models.article_tag import ArticleTag
from app.db.models.character_inventory import CharacterInventory
from app.db.models.enums import UserRole, VisibilityType


# ── CRUD de Pastas ─────────────────────────────────────────────────────────────

async def criar_pasta(
    db: AsyncSession,
    world_id: uuid.UUID,
    name: str,
    parent_id: int | None = None,
) -> ArticleFolder:
    """Cria uma pasta de artigos no mundo."""
    folder = ArticleFolder(
        world_id=world_id,
        name=name,
        parent_id=parent_id,
    )
    db.add(folder)
    await db.flush()
    return folder


async def listar_pastas(
    db: AsyncSession,
    world_id: uuid.UUID,
) -> Sequence[ArticleFolder]:
    """Lista todas as pastas do mundo."""
    stmt = (
        select(ArticleFolder)
        .where(ArticleFolder.world_id == world_id)
        .order_by(ArticleFolder.name.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def buscar_pasta(
    db: AsyncSession,
    folder_id: int,
    world_id: uuid.UUID,
) -> ArticleFolder | None:
    """Busca uma pasta por ID e world_id."""
    stmt = select(ArticleFolder).where(
        ArticleFolder.id == folder_id,
        ArticleFolder.world_id == world_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def atualizar_pasta(
    db: AsyncSession,
    folder: ArticleFolder,
    *,
    name: str | None = None,
    parent_id: int | None = ...,
) -> ArticleFolder:
    """Atualiza nome e/ou parent_id de uma pasta."""
    if name is not None:
        folder.name = name
    if parent_id is not ...:
        folder.parent_id = parent_id
    await db.flush()
    return folder


async def deletar_pasta(
    db: AsyncSession,
    folder: ArticleFolder,
) -> None:
    """Remove uma pasta."""
    await db.delete(folder)


# ── CRUD de Artigos ────────────────────────────────────────────────────────────

def format_sections_to_content(sections: list[dict]) -> str:
    """Converte lista legada de seções em um texto Markdown contínuo."""
    blocks = []
    for sec in sections:
        t_clean = (sec.get("title") or "").strip()
        c_clean = (sec.get("content") or "").strip()
        if t_clean:
            blocks.append(f"# {t_clean}\n\n{c_clean}".strip())
        elif c_clean:
            blocks.append(c_clean)
    return "\n\n".join(b for b in blocks if b)


async def criar_artigo(
    db: AsyncSession,
    world_id: uuid.UUID,
    created_by: uuid.UUID,
    role: UserRole,
    *,
    title: str,
    folder_id: int | None = None,
    content: str = "",
    visibility: VisibilityType | None = None,
    in_game_date: str | None = None,
    in_game_sort_order: int | None = None,
    tags: list[str] = [],
    sections: list[dict] | None = None,
) -> Article:
    """
    Cria um artigo com texto Markdown e tags em cascata.
    Aplica RN-01/RN-02 se visibility nao for informado.
    """
    if visibility is None:
        visibility = VisibilityType.NULA if role == UserRole.MESTRE else VisibilityType.TOTAL

    if not content and sections:
        content = format_sections_to_content(sections)

    article = Article(
        world_id=world_id,
        folder_id=folder_id,
        title=title,
        content=content,
        visibility=visibility,
        in_game_date=in_game_date,
        in_game_sort_order=in_game_sort_order,
        created_by=created_by,
    )
    db.add(article)
    await db.flush()

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
    folder_id: int | None = None,
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

    if folder_id is not None:
        stmt = stmt.where(Article.folder_id == folder_id)

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
    """Busca um artigo com tags e inventory carregados."""
    stmt = (
        select(Article)
        .options(
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
    folder_id: int | None = ...,
    content: str | None = None,
    visibility: VisibilityType | None = None,
    in_game_date: str | None = ...,
    in_game_sort_order: int | None = ...,
    tags: list[str] | None = None,
    sections: list[dict] | None = None,
) -> Article:
    """
    Atualiza um artigo.
    """
    if title is not None:
        article.title = title
    if folder_id is not ...:
        article.folder_id = folder_id
    if content is not None:
        article.content = content
    elif sections is not None:
        article.content = format_sections_to_content(sections)
    if visibility is not None:
        article.visibility = visibility
    if in_game_date is not ...:
        article.in_game_date = in_game_date
    if in_game_sort_order is not ...:
        article.in_game_sort_order = in_game_sort_order

    # Replace tags
    if tags is not None:
        for tag in list(article.tags):
            await db.delete(tag)
        await db.flush()
        for tag_name in tags:
            db.add(ArticleTag(article_id=article.id, name=tag_name))

    await db.flush()
    return article


async def atualizar_conteudo_artigo(
    db: AsyncSession,
    article_id: uuid.UUID,
    world_id: uuid.UUID,
    content: str,
) -> Article:
    """
    Atualiza unicamente o campo `content` do artigo (autosave acelerado de baixa latência).
    """
    from fastapi import HTTPException, status

    stmt = select(Article).where(Article.id == article_id, Article.world_id == world_id)
    res = await db.execute(stmt)
    article = res.scalar_one_or_none()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artigo não encontrado."
        )

    article.content = content
    await db.flush()
    return article


async def deletar_artigo(
    db: AsyncSession,
    article: Article,
) -> None:
    """Remove um artigo (CASCADE deleta tags, inventory)."""
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


# ── Wikilinks, Autocomplete & Backlinks ───────────────────────────────────────

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
    Busca todos os artigos no mundo que mencionam o título do artigo atual no seu conteúdo.
    Retorna lista de referências (backlinks) sanitizadas respeitando a Névoa de Guerra.
    """
    # 1. Obter o artigo alvo para saber o seu título
    target_article = await buscar_artigo(db, article_id, world_id)
    if not target_article:
        return []

    target_title = target_article.title.lower()

    # 2. Buscar artigos do mesmo mundo (excluindo o próprio artigo)
    stmt = select(Article).where(Article.world_id == world_id, Article.id != article_id)

    if role == UserRole.JOGADOR:
        stmt = stmt.where(Article.visibility != VisibilityType.NULA)

    result = await db.execute(stmt)
    articles = result.scalars().all()

    backlinks = []
    for source_article in articles:
        content_lower = (source_article.content or "").lower()
        if f"[[{target_title}" in content_lower:
            is_locked = role == UserRole.JOGADOR and source_article.visibility == VisibilityType.PARCIAL

            idx = content_lower.find(f"[[{target_title}")
            start = max(0, idx - 40)
            end = min(len(source_article.content), idx + len(target_title) + 50)
            snippet = ("..." if start > 0 else "") + source_article.content[start:end] + ("..." if end < len(source_article.content) else "")

            backlinks.append({
                "article_id": source_article.id,
                "title": source_article.title,
                "visibility": source_article.visibility,
                "section_title": "",
                "snippet": snippet if not is_locked else "Conteúdo protegido por Névoa de Guerra Parcial.",
                "is_locked": is_locked,
            })

    return backlinks


# ── Gestão de Permissões ──────────────────────────────────────────────────────

async def obter_permissoes_artigo(
    db: AsyncSession, world_id: uuid.UUID, article_id: uuid.UUID
) -> list[dict]:
    """Retorna a matriz de permissões por usuário para um artigo."""
    from app.db.models.world_member import WorldMember
    from app.db.models.user import User
    from app.db.models.article_user_permission import ArticleUserPermission

    art_res = await db.execute(select(Article).where(Article.id == article_id))
    article = art_res.scalar_one_or_none()
    default_vis = article.visibility if article else VisibilityType.NULA

    members_res = await db.execute(
        select(User, WorldMember)
        .join(WorldMember, User.id == WorldMember.user_id)
        .where(WorldMember.world_id == world_id)
    )
    members = members_res.all()

    perms_res = await db.execute(
        select(ArticleUserPermission).where(ArticleUserPermission.article_id == article_id)
    )
    perms_map = {p.user_id: p.visibility for p in perms_res.scalars().all()}

    result = []
    for user, member in members:
        if member.role == UserRole.MESTRE or (article and article.created_by == user.id):
            vis = VisibilityType.TOTAL
        else:
            vis = perms_map.get(user.id, default_vis)

        result.append({
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "visibility": vis,
        })
    return result


async def atualizar_permissoes_artigo(
    db: AsyncSession, article_id: uuid.UUID, permissions: list[dict]
) -> None:
    """Atualiza a matriz de permissões por usuário de um artigo."""
    from app.db.models.article_user_permission import ArticleUserPermission

    for p in permissions:
        u_id = uuid.UUID(str(p["user_id"]))
        vis = VisibilityType(p["visibility"])

        stmt = select(ArticleUserPermission).where(
            ArticleUserPermission.article_id == article_id,
            ArticleUserPermission.user_id == u_id,
        )
        res = await db.execute(stmt)
        perm_obj = res.scalar_one_or_none()

        if perm_obj:
            perm_obj.visibility = vis
        else:
            db.add(ArticleUserPermission(
                article_id=article_id,
                user_id=u_id,
                visibility=vis,
            ))
    await db.flush()
