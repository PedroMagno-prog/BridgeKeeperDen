"""Serviço assíncrono de Inventários, Grupos e Itens."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.article import Article
from app.db.models.enums import UserRole, VisibilityType
from app.db.models.inventory import Inventory
from app.db.models.inventory_group import InventoryGroup
from app.db.models.inventory_item import InventoryItem


# ── Grupos de Inventário ───────────────────────────────────────────────────────

async def criar_grupo_inventario(
    db: AsyncSession,
    world_id: uuid.UUID,
    created_by: uuid.UUID,
    role: UserRole,
    *,
    name: str,
    description: str | None = None,
    visibility: VisibilityType | None = None,
    icon: str | None = "folder",
) -> InventoryGroup:
    """Cria um grupo de inventários."""
    if visibility is None:
        visibility = VisibilityType.NULA if role == UserRole.MESTRE else VisibilityType.TOTAL

    group = InventoryGroup(
        world_id=world_id,
        name=name,
        description=description,
        visibility=visibility,
        icon=icon or "folder",
        created_by=created_by,
    )
    db.add(group)
    await db.flush()
    return group


async def listar_grupos_inventario(
    db: AsyncSession,
    world_id: uuid.UUID,
    role: UserRole,
) -> Sequence[InventoryGroup]:
    """Lista grupos de inventário do mundo com pré-carregamento dos inventários e itens."""
    stmt = (
        select(InventoryGroup)
        .options(
            selectinload(InventoryGroup.inventories).selectinload(Inventory.items).selectinload(InventoryItem.article).selectinload(Article.tags)
        )
        .where(InventoryGroup.world_id == world_id)
    )

    if role == UserRole.JOGADOR:
        stmt = stmt.where(InventoryGroup.visibility != VisibilityType.NULA)

    stmt = stmt.order_by(InventoryGroup.name.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def buscar_grupo_inventario(
    db: AsyncSession,
    group_id: uuid.UUID,
    world_id: uuid.UUID,
    populate_existing: bool = False,
) -> InventoryGroup | None:
    """Busca um grupo pelo ID."""
    stmt = (
        select(InventoryGroup)
        .options(
            selectinload(InventoryGroup.inventories).selectinload(Inventory.items).selectinload(InventoryItem.article).selectinload(Article.tags)
        )
        .where(InventoryGroup.id == group_id, InventoryGroup.world_id == world_id)
    )
    if populate_existing:
        stmt = stmt.execution_options(populate_existing=True)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def atualizar_grupo_inventario(
    db: AsyncSession,
    group: InventoryGroup,
    *,
    name: str | None = None,
    description: str | None = ...,
    visibility: VisibilityType | None = None,
    icon: str | None = ...,
) -> InventoryGroup:
    """Atualiza dados de um grupo."""
    if name is not None:
        group.name = name
    if description is not ...:
        group.description = description
    if visibility is not None:
        group.visibility = visibility
    if icon is not ...:
        group.icon = icon

    await db.flush()
    return group


async def deletar_grupo_inventario(
    db: AsyncSession,
    group: InventoryGroup,
) -> None:
    """Remove um grupo de inventário (CASCADE deleta os inventários associados)."""
    await db.delete(group)


# ── Inventários ───────────────────────────────────────────────────────────────

async def criar_inventario(
    db: AsyncSession,
    world_id: uuid.UUID,
    created_by: uuid.UUID,
    role: UserRole,
    *,
    name: str,
    group_id: uuid.UUID | None = None,
    owner_article_id: uuid.UUID | None = None,
    description: str | None = None,
    limit: int | None = None,
    visibility: VisibilityType | None = None,
) -> Inventory:
    """Cria um inventário individual."""
    if visibility is None:
        visibility = VisibilityType.NULA if role == UserRole.MESTRE else VisibilityType.TOTAL

    inventory = Inventory(
        world_id=world_id,
        group_id=group_id,
        owner_article_id=owner_article_id,
        name=name,
        description=description,
        limit=limit,
        visibility=visibility,
        created_by=created_by,
    )
    db.add(inventory)
    await db.flush()
    return inventory


async def listar_inventarios(
    db: AsyncSession,
    world_id: uuid.UUID,
    role: UserRole,
    group_id: uuid.UUID | None = None,
) -> Sequence[Inventory]:
    """Lista inventários do mundo (ou de um grupo específico)."""
    stmt = (
        select(Inventory)
        .options(
            selectinload(Inventory.items).selectinload(InventoryItem.article).selectinload(Article.tags)
        )
        .where(Inventory.world_id == world_id)
    )

    if group_id is not None:
        stmt = stmt.where(Inventory.group_id == group_id)

    if role == UserRole.JOGADOR:
        stmt = stmt.where(Inventory.visibility != VisibilityType.NULA)

    stmt = stmt.order_by(Inventory.name.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def buscar_inventario(
    db: AsyncSession,
    inventory_id: uuid.UUID,
    world_id: uuid.UUID,
    populate_existing: bool = False,
) -> Inventory | None:
    """Busca um inventário detalhado."""
    stmt = (
        select(Inventory)
        .options(
            selectinload(Inventory.items).selectinload(InventoryItem.article).selectinload(Article.tags)
        )
        .where(Inventory.id == inventory_id, Inventory.world_id == world_id)
    )
    if populate_existing:
        stmt = stmt.execution_options(populate_existing=True)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def atualizar_inventario(
    db: AsyncSession,
    inventory: Inventory,
    *,
    name: str | None = None,
    group_id: uuid.UUID | None = ...,
    owner_article_id: uuid.UUID | None = ...,
    description: str | None = ...,
    limit: int | None = ...,
    visibility: VisibilityType | None = None,
) -> Inventory:
    """Atualiza dados de um inventário."""
    if name is not None:
        inventory.name = name
    if group_id is not ...:
        inventory.group_id = group_id
    if owner_article_id is not ...:
        inventory.owner_article_id = owner_article_id
    if description is not ...:
        inventory.description = description
    if limit is not ...:
        inventory.limit = limit
    if visibility is not None:
        inventory.visibility = visibility

    await db.flush()
    return inventory


async def deletar_inventario(
    db: AsyncSession,
    inventory: Inventory,
) -> None:
    """Deleta um inventário."""
    await db.delete(inventory)


# ── Itens de Inventário ───────────────────────────────────────────────────────

async def adicionar_item(
    db: AsyncSession,
    inventory_id: uuid.UUID,
    *,
    article_id: uuid.UUID | None = None,
    custom_name: str | None = None,
    quantity: int = 1,
    notes: str | None = None,
    order_index: int = 0,
) -> InventoryItem:
    """Adiciona um novo slot/item no inventário."""
    item = InventoryItem(
        inventory_id=inventory_id,
        article_id=article_id,
        custom_name=custom_name,
        quantity=quantity,
        notes=notes,
        order_index=order_index,
    )
    db.add(item)
    await db.flush()
    return item


async def buscar_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    inventory_id: uuid.UUID,
) -> InventoryItem | None:
    """Busca um item específico."""
    stmt = (
        select(InventoryItem)
        .options(selectinload(InventoryItem.article).selectinload(Article.tags))
        .where(InventoryItem.id == item_id, InventoryItem.inventory_id == inventory_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def atualizar_item(
    db: AsyncSession,
    item: InventoryItem,
    *,
    article_id: uuid.UUID | None = ...,
    custom_name: str | None = ...,
    quantity: int | None = None,
    notes: str | None = ...,
    order_index: int | None = None,
) -> InventoryItem:
    """Atualiza dados de um item."""
    if article_id is not ...:
        item.article_id = article_id
    if custom_name is not ...:
        item.custom_name = custom_name
    if quantity is not None:
        item.quantity = quantity
    if notes is not ...:
        item.notes = notes
    if order_index is not None:
        item.order_index = order_index

    await db.flush()
    return item


async def remover_item(
    db: AsyncSession,
    item: InventoryItem,
) -> None:
    """Remove um item do inventário."""
    await db.delete(item)
