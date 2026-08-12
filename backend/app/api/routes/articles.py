"""Rotas do Modulo A: Artigos (Codex & Wiki) — 6 endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.world_access import WorldContext, get_world_ctx
from app.db.models.enums import UserRole
from app.schemas.article import (
    ArticleCreate,
    ArticleDetailOut,
    ArticleListOut,
    ArticleResolveOut,
    ArticleUpdate,
    BacklinkOut,
    InventoryItemOut,
    InventoryUpdateInput,
    MentionSuggestionOut,
    ObsidianImportResultOut,
)
from app.schemas.permission import UserPermissionOut, ResourcePermissionsUpdateInput
from app.services import article_service, obsidian_import_service
from app.services.fog_of_war import sanitize_article_detail, sanitize_article_for_list

router = APIRouter()


# ── GET /worlds/{world_id}/articles/resolve ───────────────────────────────────

@router.get(
    "/resolve",
    response_model=ArticleResolveOut,
    summary="Resolve rapidamente um Wikilink pelo título",
)
async def resolver_wikilink(
    title: str,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Verifica se um artigo existe pelo título e retorna seu ID/visibilidade."""
    return await article_service.resolver_artigo_por_titulo(db, ctx.world_id, title, ctx.role)


# ── GET /worlds/{world_id}/articles/search-mentions ───────────────────────────

@router.get(
    "/search-mentions",
    response_model=list[MentionSuggestionOut],
    summary="Autocomplete de sugestões para menções e Wikilinks",
)
async def autocomplete_mencoes(
    query: str = "",
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Busca até 10 artigos por título para autocomplete no editor de texto."""
    articles = await article_service.buscar_mencao_sugestoes(db, ctx.world_id, query, ctx.role)
    return [
        MentionSuggestionOut(
            id=a.id,
            title=a.title,
            visibility=a.visibility,
            tags=[t.name for t in a.tags] if hasattr(a, "tags") and a.tags else [],
        )
        for a in articles
    ]


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
    Fog of War: JOGADOR nao ve artigos NULA; PARCIAL retorna apenas titulo; CONTROLADO/TOTAL retorna completo.
    """
    articles = await article_service.listar_artigos(
        db, ctx.world_id, ctx.role, tag_filter=tag, search=search,
    )

    from app.db.models.article_user_permission import ArticleUserPermission
    perm_res = await db.execute(
        select(ArticleUserPermission.article_id, ArticleUserPermission.visibility).where(
            ArticleUserPermission.user_id == ctx.user.id
        )
    )
    user_perms = {row[0]: row[1] for row in perm_res.all()}

    result = []
    for article in articles:
        spec_perm = user_perms.get(article.id)
        sanitized = sanitize_article_for_list(article, ctx.role, ctx.user.id, spec_perm)
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

    loaded = await article_service.buscar_artigo(db, article.id, ctx.world_id)
    return sanitize_article_detail(loaded, ctx.role, ctx.user.id)


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

    from app.db.models.article_user_permission import ArticleUserPermission
    perm_res = await db.execute(
        select(ArticleUserPermission.visibility).where(
            ArticleUserPermission.article_id == article_id,
            ArticleUserPermission.user_id == ctx.user.id,
        )
    )
    spec_perm = perm_res.scalar_one_or_none()
    print("DEBUG_BUSCAR_ARTIGO:", "user:", ctx.user.id, "spec_perm:", spec_perm, "type:", type(spec_perm))

    sanitized = sanitize_article_detail(article, ctx.role, ctx.user.id, spec_perm)
    print("DEBUG_SANITIZED:", sanitized)
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

    # Verificar se usuário tem permissão CONTROLADO (Somente Leitura)
    from app.db.models.article_user_permission import ArticleUserPermission
    from app.services.fog_of_war import resolve_effective_visibility

    perm_res = await db.execute(
        select(ArticleUserPermission.visibility).where(
            ArticleUserPermission.article_id == article_id,
            ArticleUserPermission.user_id == ctx.user.id,
        )
    )
    spec_perm = perm_res.scalar_one_or_none()
    eff_vis, can_edit, can_delete = resolve_effective_visibility(
        article.visibility, article.created_by, ctx.user.id, ctx.role, spec_perm
    )

    if not can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sua permissão neste recurso é de Somente Leitura (CONTROLADO)."
        )

    # Apenas MESTRE pode alterar visibilidade
    if body.visibility is not None and not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode alterar a visibilidade.")

    sections_data = [s.model_dump() for s in body.sections] if body.sections is not None else None
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

    loaded = await article_service.buscar_artigo(
        db, article_id, ctx.world_id, populate_existing=True
    )
    return sanitize_article_detail(loaded, ctx.role, ctx.user.id, spec_perm)


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
    """Remove um artigo. Apenas MESTRE ou criador com permissão TOTAL."""
    article = await article_service.buscar_artigo(db, article_id, ctx.world_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artigo nao encontrado.")

    from app.db.models.article_user_permission import ArticleUserPermission
    from app.services.fog_of_war import resolve_effective_visibility

    perm_res = await db.execute(
        select(ArticleUserPermission.visibility).where(
            ArticleUserPermission.article_id == article_id,
            ArticleUserPermission.user_id == ctx.user.id,
        )
    )
    spec_perm = perm_res.scalar_one_or_none()
    eff_vis, can_edit, can_delete = resolve_effective_visibility(
        article.visibility, article.created_by, ctx.user.id, ctx.role, spec_perm
    )

    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para deletar este artigo (CONTROLADO)."
        )

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


# ── GET /worlds/{world_id}/articles/{article_id}/backlinks ────────────────────

@router.get(
    "/{article_id}/backlinks",
    response_model=list[BacklinkOut],
    summary="Obtém lista de backlinks/citações que apontam para este artigo",
)
async def buscar_backlinks(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Retorna referências de outros artigos que citam o artigo atual no formato [[Título]]."""
    return await article_service.buscar_backlinks(db, ctx.world_id, article_id, ctx.role)


# ── POST /worlds/{world_id}/articles/import/obsidian ─────────────────────────

@router.post(
    "/import/obsidian",
    response_model=ObsidianImportResultOut,
    status_code=status.HTTP_201_CREATED,
    summary="Importa um cofre Obsidian em formato .zip",
)
async def importar_cofre_obsidian(
    file: UploadFile = File(...),
    use_folders_as_tags: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """
    Importa um cofre do Obsidian (.zip) no Codex do mundo ativo.
    Apenas o Mestre pode importar.
    Aplica Obscurecimento Total (Visão Nula) por padrão para resguardar a lore.
    """
    if not ctx.is_mestre:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o Mestre do mundo pode importar cofres de notas."
        )

    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo enviado deve ser do tipo .zip."
        )

    zip_bytes = await file.read()
    res = await obsidian_import_service.processar_zip_obsidian(
        db,
        ctx.world_id,
        ctx.user.id,
        zip_bytes,
        use_folders_as_tags=use_folders_as_tags,
    )
    await db.commit()

    return ObsidianImportResultOut(
        imported_count=res["imported_count"],
        skipped_count=res["skipped_count"],
        message=f"{res['imported_count']} notas importadas com sucesso com Obscurecimento Total (Visão Nula).",
    )


# ── GET /worlds/{world_id}/articles/{article_id}/permissions ─────────────────

@router.get(
    "/{article_id}/permissions",
    response_model=list[UserPermissionOut],
    summary="Obtém a matriz de permissões por usuário de um artigo",
)
async def obter_permissoes_artigo(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Apenas Mestre pode consultar a matriz de permissões por jogador."""
    if not ctx.is_mestre:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o Mestre pode gerenciar permissões individuais."
        )
    perms = await article_service.obter_permissoes_artigo(db, ctx.world_id, article_id)
    return [UserPermissionOut(**p) for p in perms]


# ── PUT /worlds/{world_id}/articles/{article_id}/permissions ─────────────────

@router.put(
    "/{article_id}/permissions",
    status_code=status.HTTP_200_OK,
    summary="Atualiza a matriz de permissões por usuário de um artigo",
)
async def atualizar_permissoes_artigo(
    article_id: uuid.UUID,
    body: ResourcePermissionsUpdateInput,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Apenas Mestre pode salvar a matriz de permissões por jogador."""
    if not ctx.is_mestre:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o Mestre pode gerenciar permissões individuais."
        )
    await article_service.atualizar_permissoes_artigo(
        db, article_id, [p.model_dump() for p in body.permissions]
    )
    await db.commit()
    return {"message": "Permissões atualizadas com sucesso."}


# ── POST /worlds/{world_id}/articles/{article_id}/sections/{section_id}/image ──

@router.post(
    "/{article_id}/sections/{section_id}/image",
    summary="Anexa/atualiza imagem complementar em uma seção de artigo",
)
async def anexar_imagem_secao(
    article_id: uuid.UUID,
    section_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """
    Anexa uma imagem à seção de artigo.
    Imagens > 5MB são otimizadas/redimensionadas via Pillow para formato WebP.
    """
    from app.db.models.article_section import ArticleSection

    # Buscar seção
    stmt = select(ArticleSection).where(
        ArticleSection.id == section_id,
        ArticleSection.article_id == article_id,
    )
    res = await db.execute(stmt)
    section = res.scalar_one_or_none()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seção de artigo não encontrada."
        )

    file_bytes = await file.read()
    image_url = await article_service.anexar_imagem_secao(
        db, section, file_bytes, file.filename or "section_img.jpg"
    )
    await db.commit()

    return {"image_url": image_url}
