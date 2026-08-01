"""Rotas do Modulo A: Artigos (Codex & Wiki) — 6 endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.world_access import WorldContext, get_world_ctx
from app.db.models.enums import UserRole
from app.schemas.article import (
    ArticleCreate,
    ArticleDetailOut,
    ArticleListOut,
    ArticleUpdate,
    InventoryItemOut,
    InventoryUpdateInput,
)
from app.services import article_service
from app.services.fog_of_war import sanitize_article_detail, sanitize_article_for_list

router = APIRouter()


# ── GET /worlds/{world_id}/articles ───────────────────────────────────────────

@router.get("/", response_model=list[ArticleListOut], summary="Lista artigos do mundo")
async def listar_artigos(
    tag: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """
    Lista artigos com suporte a filtros por tag e busca textual.
    Fog of War: JOGADOR nao ve artigos NULA; PARCIAL retorna apenas titulo.
    """
    articles = await article_service.listar_artigos(
        db, ctx.world_id, ctx.role, tag_filter=tag, search=search,
    )

    result = []
    for article in articles:
        sanitized = sanitize_article_for_list(article, ctx.role)
        if sanitized is not None:
            result.append(sanitized)

    return result


# ── POST /worlds/{world_id}/articles ──────────────────────────────────────────

@router.post(
    "/",
    response_model=ArticleDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo artigo",
)
async def criar_artigo(
    body: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """
    Cria artigo com sections e tags.
    RN-01: MESTRE -> visibility default NULA.
    RN-02: JOGADOR -> visibility default TOTAL.
    """
    article = await article_service.criar_artigo(
        db,
        ctx.world_id,
        ctx.user.id,
        ctx.role,
        title=body.title,
        visibility=body.visibility,
        in_game_date=body.in_game_date,
        in_game_sort_order=body.in_game_sort_order,
        tags=body.tags,
        sections=[s.model_dump() for s in body.sections],
    )
    await db.commit()

    # Recarregar com relacionamentos
    loaded = await article_service.buscar_artigo(db, article.id, ctx.world_id)
    return sanitize_article_detail(loaded, ctx.role)


# ── GET /worlds/{world_id}/articles/{article_id} ─────────────────────────────

@router.get("/{article_id}", response_model=ArticleDetailOut, summary="Detalhe do artigo")
async def buscar_artigo(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Obtem o detalhe de um artigo com sections, tags e inventory."""
    article = await article_service.buscar_artigo(db, article_id, ctx.world_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artigo nao encontrado.")

    sanitized = sanitize_article_detail(article, ctx.role)
    if sanitized is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artigo nao encontrado.")

    return sanitized


# ── PUT /worlds/{world_id}/articles/{article_id} ─────────────────────────────

@router.put("/{article_id}", response_model=ArticleDetailOut, summary="Atualiza artigo")
async def atualizar_artigo(
    article_id: uuid.UUID,
    body: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Atualiza titulo, tags, visibilidade e secoes de um artigo."""
    article = await article_service.buscar_artigo(db, article_id, ctx.world_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artigo nao encontrado.")

    # Apenas MESTRE ou criador pode editar
    if not ctx.is_mestre and article.created_by != ctx.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissao para editar este artigo.")

    # Apenas MESTRE pode alterar visibilidade
    if body.visibility is not None and not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode alterar a visibilidade.")

    sections_data = [s.model_dump() for s in body.sections] if body.sections is not None else None

    # Usa model_fields_set para saber se campos opcionais foram explicitamente enviados
    fields_set = body.model_fields_set

    await article_service.atualizar_artigo(
        db,
        article,
        title=body.title,
        visibility=body.visibility,
        in_game_date=body.in_game_date if "in_game_date" in fields_set else ...,
        in_game_sort_order=body.in_game_sort_order if "in_game_sort_order" in fields_set else ...,
        tags=body.tags,
        sections=sections_data,
    )
    await db.commit()

    # article.tags e article.sections ja estao atualizados na identity map
    return sanitize_article_detail(article, ctx.role)


# ── DELETE /worlds/{world_id}/articles/{article_id} ──────────────────────────

@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um artigo",
)
async def deletar_artigo(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Remove um artigo. Apenas MESTRE ou criador do artigo."""
    article = await article_service.buscar_artigo(db, article_id, ctx.world_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artigo nao encontrado.")

    if not ctx.is_mestre and article.created_by != ctx.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissao para deletar este artigo.")

    await article_service.deletar_artigo(db, article)
    await db.commit()


# ── POST /worlds/{world_id}/articles/{article_id}/inventory ──────────────────

@router.post(
    "/{article_id}/inventory",
    response_model=list[InventoryItemOut],
    summary="Atualiza inventario do personagem",
)
async def atualizar_inventario(
    article_id: uuid.UUID,
    body: InventoryUpdateInput,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Adiciona/atualiza os itens de mochila para artigos de personagens."""
    article = await article_service.buscar_artigo(db, article_id, ctx.world_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artigo nao encontrado.")

    items = await article_service.atualizar_inventario(
        db, article_id, [item.model_dump() for item in body.items],
    )
    await db.commit()

    # Refresh cada item para garantir que os IDs gerados estao disponiveis
    for item in items:
        await db.refresh(item)

    return [
        InventoryItemOut(
            id=item.id,
            item_name=item.item_name,
            quantity=item.quantity,
            description=item.description,
        )
        for item in items
    ]
