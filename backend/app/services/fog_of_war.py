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


def sanitize_article_for_list(article: Any, role: UserRole) -> dict | None:
    """
    Sanitiza um artigo para exibicao em listagem.

    - MESTRE: retorna todos os campos.
    - JOGADOR + NULA: retorna None (excluido da lista).
    - JOGADOR + PARCIAL: retorna id, title, visibility, is_locked=True.
    - JOGADOR + TOTAL: retorna campos publicos completos.
    """
    if role == UserRole.MESTRE:
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
        }

    # JOGADOR
    if article.visibility == VisibilityType.NULA:
        return None

    if article.visibility == VisibilityType.PARCIAL:
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
        }

    # TOTAL
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
    }


def sanitize_article_detail(article: Any, role: UserRole) -> dict | None:
    """
    Sanitiza um artigo para exibicao de detalhe (com sections).

    - MESTRE: retorna tudo.
    - JOGADOR + NULA: retorna None.
    - JOGADOR + PARCIAL: retorna apenas id, title, is_locked=True.
    - JOGADOR + TOTAL: retorna tudo.
    """
    if role == UserRole.MESTRE:
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
        }

    if article.visibility == VisibilityType.NULA:
        return None

    if article.visibility == VisibilityType.PARCIAL:
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
        }

    # TOTAL
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
    }


def sanitize_pin(pin: Any, role: UserRole) -> dict | None:
    """
    Sanitiza um pin de mapa.

    - MESTRE: retorna tudo.
    - JOGADOR + NULA: retorna None (pin invisivel).
    - JOGADOR + PARCIAL: titulo visivel, icone '?', sem target links.
    - JOGADOR + TOTAL: retorna tudo.
    """
    if role == UserRole.MESTRE:
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
            "is_locked": False,
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
            "is_locked": True,
        }

    # TOTAL
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
        "is_locked": False,
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
