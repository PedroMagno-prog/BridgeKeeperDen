"""
Fog of War Sanitizer.

Centraliza a logica de filtragem de visibilidade para todas as entidades
do sistema. Garante que dados com Visao Nula NUNCA cheguem ao jogador
e que dados com Visao Parcial cheguem apenas com titulo (sem conteudo).

Ref: Documento 01 (Secao 2.2) e Documento 03 (Passo 2).
"""
from __future__ import annotations

from typing import Any

from app.db.models.enums import UserRole, VisibilityType


def resolve_effective_visibility(
    resource_visibility: VisibilityType,
    created_by: Any,
    user_id: Any,
    role: UserRole,
    specific_perm: VisibilityType | str | None = None,
) -> tuple[VisibilityType, bool, bool]:
    """
    Resolve a visibilidade efetiva e as permissões de edição/exclusão (can_edit, can_delete).
    Ordem de precedência:
    1. MESTRE -> TOTAL (can_edit=True, can_delete=True)
    2. Criador (created_by == user_id) -> TOTAL (can_edit=True, can_delete=True)
    3. Permissão Específica do Usuário em tabela de permissões -> specific_perm
    4. Visibilidade Padrão do Recurso -> resource_visibility
    """
    if role == UserRole.MESTRE:
        return VisibilityType.TOTAL, True, True

    if created_by and str(created_by) == str(user_id):
        return VisibilityType.TOTAL, True, True

    raw_eff = specific_perm if specific_perm is not None else resource_visibility
    if isinstance(raw_eff, str):
        try:
            eff = VisibilityType(raw_eff)
        except ValueError:
            eff = VisibilityType.NULA
    else:
        eff = raw_eff

    if eff == VisibilityType.TOTAL:
        return VisibilityType.TOTAL, True, True
    elif eff == VisibilityType.CONTROLADO:
        return VisibilityType.CONTROLADO, False, False
    elif eff == VisibilityType.PARCIAL:
        return VisibilityType.PARCIAL, False, False
    else:  # NULA
        return VisibilityType.NULA, False, False


def sanitize_article_for_list(
    article: Any, role: UserRole, user_id: Any = None, specific_perm: VisibilityType | None = None
) -> dict | None:
    """
    Sanitiza um artigo para exibição em listagem.
    """
    eff_vis, can_edit, can_delete = resolve_effective_visibility(
        article.visibility, article.created_by, user_id, role, specific_perm
    )

    if eff_vis == VisibilityType.NULA:
        return None

    if eff_vis == VisibilityType.PARCIAL:
        return {
            "id": article.id,
            "title": article.title,
            "visibility": article.visibility,
            "in_game_date": None,
            "in_game_sort_order": None,
            "tags": [],
            "created_by": None,
            "created_at": None,
            "updated_at": None,
            "is_locked": True,
            "can_edit": False,
            "can_delete": False,
        }

    # CONTROLADO ou TOTAL
    return {
        "id": article.id,
        "title": article.title,
        "visibility": article.visibility,
        "in_game_date": article.in_game_date,
        "in_game_sort_order": article.in_game_sort_order,
        "tags": [t.name for t in article.tags],
        "created_by": article.created_by,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
        "is_locked": False,
        "can_edit": can_edit,
        "can_delete": can_delete,
    }


def sanitize_article_detail(
    article: Any, role: UserRole, user_id: Any = None, specific_perm: VisibilityType | None = None
) -> dict | None:
    """
    Sanitiza um artigo para exibição de detalhe (com sections e image_url).
    """
    eff_vis, can_edit, can_delete = resolve_effective_visibility(
        article.visibility, article.created_by, user_id, role, specific_perm
    )

    if eff_vis == VisibilityType.NULA:
        return None

    if eff_vis == VisibilityType.PARCIAL:
        return {
            "id": article.id,
            "title": article.title,
            "visibility": article.visibility,
            "in_game_date": None,
            "in_game_sort_order": None,
            "tags": [],
            "sections": [],
            "inventory_items": [],
            "created_by": None,
            "created_at": None,
            "updated_at": None,
            "is_locked": True,
            "can_edit": False,
            "can_delete": False,
        }

    # CONTROLADO ou TOTAL (ambos recebem o conteúdo completo!)
    return {
        "id": article.id,
        "title": article.title,
        "visibility": article.visibility,
        "in_game_date": article.in_game_date,
        "in_game_sort_order": article.in_game_sort_order,
        "tags": [t.name for t in article.tags],
        "sections": [
            {
                "id": s.id,
                "title": s.title,
                "content": s.content,
                "order_index": s.order_index,
                "image_url": getattr(s, "image_url", None),
            }
            for s in article.sections
        ],
        "inventory_items": [
            {
                "id": item.id,
                "item_name": item.item_name,
                "quantity": item.quantity,
                "description": item.description,
            }
            for item in article.inventory_items
        ],
        "created_by": article.created_by,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
        "is_locked": False,
        "can_edit": can_edit,
        "can_delete": can_delete,
    }


def _get_target_article_summary(pin: Any, role: UserRole) -> dict | None:
    if not hasattr(pin, "target_article") or not pin.target_article:
        return None
    art = pin.target_article
    if role == UserRole.JOGADOR and art.visibility == VisibilityType.NULA:
        return None
    first_sec = None
    if hasattr(art, "sections") and art.sections:
        if role == UserRole.MESTRE or art.visibility == VisibilityType.TOTAL:
            first_sec = art.sections[0].content if art.sections[0].content else None
    tags = [t.name for t in art.tags] if hasattr(art, "tags") and art.tags else []
    return {
        "id": art.id,
        "title": art.title,
        "visibility": art.visibility,
        "tags": tags,
        "first_section_preview": first_sec,
    }


def sanitize_pin(pin: Any, role: UserRole, user_id: Any = None) -> dict | None:
    """
    Sanitiza um pin de mapa.

    - MESTRE: retorna tudo (com preview do artigo e titulo do sub-mapa).
    - Criador (pin.created_by == user_id): visibilidade TOTAL para o criador (can_edit=True, can_delete=True).
    - JOGADOR + NULA: retorna None (pin invisivel).
    - JOGADOR + PARCIAL: titulo visivel, icone '?', sem target links.
    - JOGADOR + CONTROLADO / TOTAL: retorna dados visíveis, sem permissão de edição.
    """
    target_map_title = pin.target_map.title if hasattr(pin, "target_map") and pin.target_map else None
    created_by_id = getattr(pin, "created_by", None)

    is_creator = bool(user_id and created_by_id and str(created_by_id) == str(user_id))
    can_edit = bool(role == UserRole.MESTRE or is_creator)
    can_delete = bool(role == UserRole.MESTRE or is_creator)

    if role == UserRole.MESTRE or is_creator:
        return {
            "id": pin.id,
            "title": pin.title,
            "x_position": float(pin.x_position),
            "y_position": float(pin.y_position),
            "icon": pin.icon,
            "color": pin.color,
            "visibility": pin.visibility,
            "layer_id": pin.layer_id,
            "target_article_id": pin.target_article_id,
            "target_map_id": pin.target_map_id,
            "target_article": _get_target_article_summary(pin, role),
            "target_map_title": target_map_title,
            "created_by": created_by_id,
            "is_locked": False,
            "can_edit": can_edit,
            "can_delete": can_delete,
        }

    if pin.visibility == VisibilityType.NULA:
        return None

    if pin.visibility == VisibilityType.PARCIAL:
        return {
            "id": pin.id,
            "title": pin.title,
            "x_position": float(pin.x_position),
            "y_position": float(pin.y_position),
            "icon": "question-icon",
            "color": "#9CA3AF",
            "visibility": pin.visibility,
            "layer_id": pin.layer_id,
            "target_article_id": None,
            "target_map_id": None,
            "target_article": None,
            "target_map_title": None,
            "created_by": created_by_id,
            "is_locked": True,
            "can_edit": False,
            "can_delete": False,
        }

    # CONTROLADO ou TOTAL para outros jogadores
    return {
        "id": pin.id,
        "title": pin.title,
        "x_position": float(pin.x_position),
        "y_position": float(pin.y_position),
        "icon": pin.icon,
        "color": pin.color,
        "visibility": pin.visibility,
        "layer_id": pin.layer_id,
        "target_article_id": pin.target_article_id,
        "target_map_id": pin.target_map_id,
        "target_article": _get_target_article_summary(pin, role),
        "target_map_title": target_map_title,
        "created_by": created_by_id,
        "is_locked": False,
        "can_edit": False,
        "can_delete": False,
    }


def sanitize_chapter(chapter: Any, role: UserRole) -> dict | None:
    """
    Sanitiza um capitulo de manuscrito.

    - MESTRE: retorna tudo.
    - JOGADOR + NULA: retorna None.
    - JOGADOR + PARCIAL: titulo visivel, content vazio.
    - JOGADOR + TOTAL: retorna tudo.
    """
    if role == UserRole.MESTRE:
        return {
            "id": chapter.id,
            "title": chapter.title,
            "content": chapter.content,
            "order_index": chapter.order_index,
            "visibility": chapter.visibility,
            "is_locked": False,
        }

    if chapter.visibility == VisibilityType.NULA:
        return None

    if chapter.visibility == VisibilityType.PARCIAL:
        return {
            "id": chapter.id,
            "title": chapter.title,
            "content": "",
            "order_index": chapter.order_index,
            "visibility": chapter.visibility,
            "is_locked": True,
        }

    # TOTAL
    return {
        "id": chapter.id,
        "title": chapter.title,
        "content": chapter.content,
        "order_index": chapter.order_index,
        "visibility": chapter.visibility,
        "is_locked": False,
    }


def sanitize_timeline_event(article: Any, role: UserRole) -> dict | None:
    """
    Sanitiza um evento da timeline (artigo com in_game_sort_order).

    - MESTRE: retorna tudo.
    - JOGADOR + NULA: retorna None.
    - JOGADOR + PARCIAL: titulo visivel, datas visiveis, sem conteudo.
    - JOGADOR + TOTAL: retorna tudo.
    """
    if role == UserRole.MESTRE:
        return {
            "article_id": article.id,
            "title": article.title,
            "in_game_date": article.in_game_date,
            "in_game_sort_order": article.in_game_sort_order,
            "visibility": article.visibility,
            "is_locked": False,
        }

    if article.visibility == VisibilityType.NULA:
        return None

    if article.visibility == VisibilityType.PARCIAL:
        return {
            "article_id": article.id,
            "title": article.title,
            "in_game_date": article.in_game_date,
            "in_game_sort_order": article.in_game_sort_order,
            "visibility": article.visibility,
            "is_locked": True,
        }

    # TOTAL
    return {
        "article_id": article.id,
        "title": article.title,
        "in_game_date": article.in_game_date,
        "in_game_sort_order": article.in_game_sort_order,
        "visibility": article.visibility,
        "is_locked": False,
    }


def sanitize_inventory_item(item: Any, role: UserRole) -> dict:
    """Sanitiza um item de inventário respeitando a visibilidade do artigo vinculado."""
    display_name = item.custom_name
    article_dict = None

    if item.article:
        if role == UserRole.JOGADOR and item.article.visibility == VisibilityType.NULA:
            display_name = item.custom_name or "Item Desconhecido (Névoa)"
            article_dict = None
        elif role == UserRole.JOGADOR and item.article.visibility == VisibilityType.PARCIAL:
            display_name = item.custom_name or item.article.title
            article_dict = {
                "id": item.article.id,
                "title": item.article.title,
                "visibility": item.article.visibility,
                "tags": [],
            }
        else:
            display_name = item.custom_name or item.article.title
            article_dict = {
                "id": item.article.id,
                "title": item.article.title,
                "visibility": item.article.visibility,
                "tags": [t.name for t in item.article.tags] if hasattr(item.article, "tags") and item.article.tags else [],
            }
    else:
        if not display_name:
            display_name = "Item Sem Nome"

    return {
        "id": item.id,
        "inventory_id": item.inventory_id,
        "article_id": item.article_id if (role == UserRole.MESTRE or not item.article or item.article.visibility != VisibilityType.NULA) else None,
        "custom_name": item.custom_name,
        "display_name": display_name,
        "quantity": item.quantity,
        "notes": item.notes if (role == UserRole.MESTRE or not item.article or item.article.visibility != VisibilityType.NULA) else None,
        "order_index": item.order_index,
        "created_at": item.created_at,
        "article": article_dict,
    }


def sanitize_inventory_detail(inventory: Any, role: UserRole) -> dict | None:
    """Sanitiza um inventário individual com seus itens."""
    if role == UserRole.MESTRE:
        items_sanitized = [sanitize_inventory_item(item, role) for item in inventory.items]
        items_count = len(inventory.items)
        is_over = bool(inventory.limit and items_count > inventory.limit)
        return {
            "id": inventory.id,
            "world_id": inventory.world_id,
            "group_id": inventory.group_id,
            "owner_article_id": inventory.owner_article_id,
            "name": inventory.name,
            "description": inventory.description,
            "limit": inventory.limit,
            "visibility": inventory.visibility,
            "items_count": items_count,
            "is_over_limit": is_over,
            "created_by": inventory.created_by,
            "created_at": inventory.created_at,
            "updated_at": inventory.updated_at,
            "items": items_sanitized,
            "is_locked": False,
        }

    if inventory.visibility == VisibilityType.NULA:
        return None

    if inventory.visibility == VisibilityType.PARCIAL:
        return {
            "id": inventory.id,
            "world_id": inventory.world_id,
            "group_id": inventory.group_id,
            "owner_article_id": None,
            "name": inventory.name,
            "description": None,
            "limit": inventory.limit,
            "visibility": inventory.visibility,
            "items_count": len(inventory.items),
            "is_over_limit": bool(inventory.limit and len(inventory.items) > inventory.limit),
            "created_by": inventory.created_by,
            "created_at": inventory.created_at,
            "updated_at": inventory.updated_at,
            "items": [],
            "is_locked": True,
        }

    # TOTAL
    items_sanitized = [sanitize_inventory_item(item, role) for item in inventory.items]
    items_count = len(inventory.items)
    is_over = bool(inventory.limit and items_count > inventory.limit)
    return {
        "id": inventory.id,
        "world_id": inventory.world_id,
        "group_id": inventory.group_id,
        "owner_article_id": inventory.owner_article_id,
        "name": inventory.name,
        "description": inventory.description,
        "limit": inventory.limit,
        "visibility": inventory.visibility,
        "items_count": items_count,
        "is_over_limit": is_over,
        "created_by": inventory.created_by,
        "created_at": inventory.created_at,
        "updated_at": inventory.updated_at,
        "items": items_sanitized,
        "is_locked": False,
    }


def sanitize_inventory_group_detail(group: Any, role: UserRole) -> dict | None:
    """Sanitiza um grupo de inventários com seus inventários associados."""
    if role == UserRole.MESTRE:
        invs = [sanitize_inventory_detail(inv, role) for inv in group.inventories]
        valid_invs = [inv for inv in invs if inv is not None]
        return {
            "id": group.id,
            "world_id": group.world_id,
            "name": group.name,
            "description": group.description,
            "visibility": group.visibility,
            "icon": group.icon,
            "inventories_count": len(valid_invs),
            "created_by": group.created_by,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "inventories": valid_invs,
            "is_locked": False,
        }

    if group.visibility == VisibilityType.NULA:
        return None

    if group.visibility == VisibilityType.PARCIAL:
        return {
            "id": group.id,
            "world_id": group.world_id,
            "name": group.name,
            "description": None,
            "visibility": group.visibility,
            "icon": group.icon,
            "inventories_count": len(group.inventories),
            "created_by": group.created_by,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "inventories": [],
            "is_locked": True,
        }

    # TOTAL
    invs = [sanitize_inventory_detail(inv, role) for inv in group.inventories]
    valid_invs = [inv for inv in invs if inv is not None]
    return {
        "id": group.id,
        "world_id": group.world_id,
        "name": group.name,
        "description": group.description,
        "visibility": group.visibility,
        "icon": group.icon,
        "inventories_count": len(valid_invs),
        "created_by": group.created_by,
        "created_at": group.created_at,
        "updated_at": group.updated_at,
        "inventories": valid_invs,
        "is_locked": False,
    }
