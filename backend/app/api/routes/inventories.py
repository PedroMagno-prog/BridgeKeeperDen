"""Rotas do Módulo de Inventários e Grupos — scoped by world_id."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.world_access import WorldContext, get_world_ctx
from app.schemas.inventory import (
    InventoryCreate,
    InventoryDetailOut,
    InventoryGroupCreate,
    InventoryGroupDetailOut,
    InventoryGroupOut,
    InventoryGroupUpdate,
    InventoryItemCreate,
    InventoryItemOut,
    InventoryItemUpdate,
    InventoryOut,
    InventoryUpdate,
)
from app.services import inventory_service
from app.services.fog_of_war import (
    sanitize_inventory_detail,
    sanitize_inventory_group_detail,
    sanitize_inventory_item,
)

router = APIRouter()


# ==============================================================================
# ── GRUPOS DE INVENTÁRIO ──────────────────────────────────────────────────────
# ==============================================================================

@router.get("/groups", response_model=list[InventoryGroupDetailOut], summary="Lista grupos de inventário")
async def listar_grupos(
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Lista grupos de inventário do mundo com inventários agregados."""
    groups = await inventory_service.listar_grupos_inventario(db, ctx.world_id, ctx.role)

    result = []
    for g in groups:
        sanitized = sanitize_inventory_group_detail(g, ctx.role)
        if sanitized is not None:
            result.append(sanitized)

    return result


@router.post(
    "/groups",
    response_model=InventoryGroupDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um grupo de inventários",
)
async def criar_grupo(
    body: InventoryGroupCreate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Cria um novo grupo de inventários."""
    group = await inventory_service.criar_grupo_inventario(
        db,
        ctx.world_id,
        ctx.user.id,
        ctx.role,
        name=body.name,
        description=body.description,
        visibility=body.visibility,
        icon=body.icon,
    )
    await db.commit()

    loaded = await inventory_service.buscar_grupo_inventario(db, group.id, ctx.world_id)
    return sanitize_inventory_group_detail(loaded, ctx.role)


@router.get("/groups/{group_id}", response_model=InventoryGroupDetailOut, summary="Detalhes do grupo")
async def buscar_grupo(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Obtém detalhes de um grupo e seus inventários."""
    group = await inventory_service.buscar_grupo_inventario(db, group_id, ctx.world_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo não encontrado.")

    sanitized = sanitize_inventory_group_detail(group, ctx.role)
    if sanitized is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo não encontrado.")

    return sanitized


@router.put("/groups/{group_id}", response_model=InventoryGroupDetailOut, summary="Atualiza grupo")
async def atualizar_grupo(
    group_id: uuid.UUID,
    body: InventoryGroupUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Atualiza dados do grupo. Mestre ou criador."""
    group = await inventory_service.buscar_grupo_inventario(db, group_id, ctx.world_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo não encontrado.")

    if not ctx.is_mestre and group.created_by != ctx.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para editar este grupo.")

    if body.visibility is not None and not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode alterar a visibilidade.")

    fields_set = body.model_fields_set

    await inventory_service.atualizar_grupo_inventario(
        db,
        group,
        name=body.name,
        description=body.description if "description" in fields_set else ...,
        visibility=body.visibility,
        icon=body.icon if "icon" in fields_set else ...,
    )
    await db.commit()

    loaded = await inventory_service.buscar_grupo_inventario(db, group_id, ctx.world_id, populate_existing=True)
    return sanitize_inventory_group_detail(loaded, ctx.role)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deleta grupo")
async def deletar_grupo(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Remove um grupo e seus inventários."""
    group = await inventory_service.buscar_grupo_inventario(db, group_id, ctx.world_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo não encontrado.")

    if not ctx.is_mestre and group.created_by != ctx.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para deletar este grupo.")

    await inventory_service.deletar_grupo_inventario(db, group)
    await db.commit()


# ==============================================================================
# ── INVENTÁRIOS ───────────────────────────────────────────────────────────────
# ==============================================================================

@router.get("/", response_model=list[InventoryDetailOut], summary="Lista inventários")
async def listar_inventarios(
    group_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Lista inventários do mundo."""
    invs = await inventory_service.listar_inventarios(db, ctx.world_id, ctx.role, group_id=group_id)

    result = []
    for inv in invs:
        sanitized = sanitize_inventory_detail(inv, ctx.role)
        if sanitized is not None:
            result.append(sanitized)

    return result


@router.post(
    "/",
    response_model=InventoryDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um inventário",
)
async def criar_inventario(
    body: InventoryCreate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Cria um novo inventário."""
    inv = await inventory_service.criar_inventario(
        db,
        ctx.world_id,
        ctx.user.id,
        ctx.role,
        name=body.name,
        group_id=body.group_id,
        owner_article_id=body.owner_article_id,
        description=body.description,
        limit=body.limit,
        visibility=body.visibility,
    )
    await db.commit()

    loaded = await inventory_service.buscar_inventario(db, inv.id, ctx.world_id)
    return sanitize_inventory_detail(loaded, ctx.role)


@router.get("/{inventory_id}", response_model=InventoryDetailOut, summary="Detalhes do inventário")
async def buscar_inventario(
    inventory_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Obtém detalhes de um inventário e seus itens."""
    inv = await inventory_service.buscar_inventario(db, inventory_id, ctx.world_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventário não encontrado.")

    sanitized = sanitize_inventory_detail(inv, ctx.role)
    if sanitized is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventário não encontrado.")

    return sanitized


@router.put("/{inventory_id}", response_model=InventoryDetailOut, summary="Atualiza inventário")
async def atualizar_inventario(
    inventory_id: uuid.UUID,
    body: InventoryUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Atualiza um inventário."""
    inv = await inventory_service.buscar_inventario(db, inventory_id, ctx.world_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventário não encontrado.")

    if not ctx.is_mestre and inv.created_by != ctx.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para editar este inventário.")

    if body.visibility is not None and not ctx.is_mestre:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o Mestre pode alterar a visibilidade.")

    fields_set = body.model_fields_set

    await inventory_service.atualizar_inventario(
        db,
        inv,
        name=body.name,
        group_id=body.group_id if "group_id" in fields_set else ...,
        owner_article_id=body.owner_article_id if "owner_article_id" in fields_set else ...,
        description=body.description if "description" in fields_set else ...,
        limit=body.limit if "limit" in fields_set else ...,
        visibility=body.visibility,
    )
    await db.commit()

    loaded = await inventory_service.buscar_inventario(db, inventory_id, ctx.world_id, populate_existing=True)
    return sanitize_inventory_detail(loaded, ctx.role)


@router.delete("/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deleta inventário")
async def deletar_inventario(
    inventory_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Remove um inventário."""
    inv = await inventory_service.buscar_inventario(db, inventory_id, ctx.world_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventário não encontrado.")

    if not ctx.is_mestre and inv.created_by != ctx.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para deletar este inventário.")

    await inventory_service.deletar_inventario(db, inv)
    await db.commit()


# ==============================================================================
# ── ITENS DO INVENTÁRIO ───────────────────────────────────────────────────────
# ==============================================================================

@router.post(
    "/{inventory_id}/items",
    response_model=InventoryItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona item ao inventário",
)
async def adicionar_item(
    inventory_id: uuid.UUID,
    body: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Adiciona um item ao inventário."""
    inv = await inventory_service.buscar_inventario(db, inventory_id, ctx.world_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventário não encontrado.")

    item = await inventory_service.adicionar_item(
        db,
        inventory_id,
        article_id=body.article_id,
        custom_name=body.custom_name,
        quantity=body.quantity,
        notes=body.notes,
        order_index=body.order_index,
    )
    await db.commit()

    loaded_item = await inventory_service.buscar_item(db, item.id, inventory_id)
    return sanitize_inventory_item(loaded_item, ctx.role)


@router.put(
    "/{inventory_id}/items/{item_id}",
    response_model=InventoryItemOut,
    summary="Atualiza item do inventário",
)
async def atualizar_item(
    inventory_id: uuid.UUID,
    item_id: uuid.UUID,
    body: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Atualiza dados de um item no inventário."""
    inv = await inventory_service.buscar_inventario(db, inventory_id, ctx.world_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventário não encontrado.")

    item = await inventory_service.buscar_item(db, item_id, inventory_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado.")

    fields_set = body.model_fields_set

    await inventory_service.atualizar_item(
        db,
        item,
        article_id=body.article_id if "article_id" in fields_set else ...,
        custom_name=body.custom_name if "custom_name" in fields_set else ...,
        quantity=body.quantity,
        notes=body.notes if "notes" in fields_set else ...,
        order_index=body.order_index,
    )
    await db.commit()

    loaded_item = await inventory_service.buscar_item(db, item_id, inventory_id)
    return sanitize_inventory_item(loaded_item, ctx.role)


@router.delete(
    "/{inventory_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove item do inventário",
)
async def remover_item(
    inventory_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """Remove um item do inventário."""
    inv = await inventory_service.buscar_inventario(db, inventory_id, ctx.world_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventário não encontrado.")

    item = await inventory_service.buscar_item(db, item_id, inventory_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado.")

    await inventory_service.remover_item(db, item)
    await db.commit()
