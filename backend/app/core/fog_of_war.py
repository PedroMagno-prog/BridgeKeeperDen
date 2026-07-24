from typing import List, Optional, Any
import uuid

from app.db.models.enums import UserRole, VisibilityType
from app.db.models.article import Article
from app.db.models.map import MapPin
from app.db.models.manuscript import ManuscriptChapter


def sanitize_article_dict(article: Article, role: UserRole) -> Optional[dict[str, Any]]:
    """
    Aplica as regras de Fog of War para serialização de um Artigo.
    
    Regras:
    - MESTRE: Acesso irrestrito a todos os campos. (is_locked = False)
    - JOGADOR + VISÃO NULA: Retorna None (Recurso oculto/não enviado no DOM/API).
    - JOGADOR + VISÃO PARCIAL: O título, tags e datas são visíveis. 
      Conteúdo interno de seções e inventários é limpo. (is_locked = True)
    - JOGADOR + VISÃO TOTAL: Acesso completo. (is_locked = False)
    """
    if role == UserRole.MESTRE:
        return {
            "id": article.id,
            "world_id": article.world_id,
            "title": article.title,
            "visibility": article.visibility,
            "in_game_date": article.in_game_date,
            "in_game_sort_order": article.in_game_sort_order,
            "created_by": article.created_by,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "is_locked": False,
            "tags": [tag.name for tag in article.tags],
            "sections": [
                {
                    "id": sec.id,
                    "article_id": sec.article_id,
                    "title": sec.title,
                    "content": sec.content,
                    "order_index": sec.order_index,
                }
                for sec in article.sections
            ],
            "inventory_items": [
                {
                    "id": item.id,
                    "article_id": item.article_id,
                    "item_name": item.item_name,
                    "quantity": item.quantity,
                    "description": item.description,
                }
                for item in article.inventory_items
            ],
        }

    # Papel JOGADOR
    if article.visibility == VisibilityType.NULA:
        return None

    if article.visibility == VisibilityType.PARCIAL:
        return {
            "id": article.id,
            "world_id": article.world_id,
            "title": article.title,
            "visibility": article.visibility,
            "in_game_date": article.in_game_date,
            "in_game_sort_order": article.in_game_sort_order,
            "created_by": article.created_by,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "is_locked": True,
            "tags": [tag.name for tag in article.tags],
            "sections": [],
            "inventory_items": [],
        }

    # VISÃO TOTAL para Jogador
    return {
        "id": article.id,
        "world_id": article.world_id,
        "title": article.title,
        "visibility": article.visibility,
        "in_game_date": article.in_game_date,
        "in_game_sort_order": article.in_game_sort_order,
        "created_by": article.created_by,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
        "is_locked": False,
        "tags": [tag.name for tag in article.tags],
        "sections": [
            {
                "id": sec.id,
                "article_id": sec.article_id,
                "title": sec.title,
                "content": sec.content,
                "order_index": sec.order_index,
            }
            for sec in article.sections
        ],
        "inventory_items": [
            {
                "id": item.id,
                "article_id": item.article_id,
                "item_name": item.item_name,
                "quantity": item.quantity,
                "description": item.description,
            }
            for item in article.inventory_items
        ],
    }


def sanitize_pin_dict(pin: MapPin, role: UserRole) -> Optional[dict[str, Any]]:
    """
    Aplica as regras de Fog of War para serialização de um Marcador (Pin) de Mapa.
    """
    if role == UserRole.MESTRE:
        return {
            "id": pin.id,
            "map_id": pin.map_id,
            "layer_id": pin.layer_id,
            "target_article_id": pin.target_article_id,
            "target_map_id": pin.target_map_id,
            "title": pin.title,
            "x_position": float(pin.x_position),
            "y_position": float(pin.y_position),
            "icon": pin.icon,
            "color": pin.color,
            "visibility": pin.visibility,
            "is_locked": False,
        }

    if pin.visibility == VisibilityType.NULA:
        return None

    if pin.visibility == VisibilityType.PARCIAL:
        return {
            "id": pin.id,
            "map_id": pin.map_id,
            "layer_id": pin.layer_id,
            "target_article_id": None,
            "target_map_id": None,
            "title": pin.title or "Local Desconhecido",
            "x_position": float(pin.x_position),
            "y_position": float(pin.y_position),
            "icon": "question-icon",
            "color": "#9CA3AF",
            "visibility": pin.visibility,
            "is_locked": True,
        }

    return {
        "id": pin.id,
        "map_id": pin.map_id,
        "layer_id": pin.layer_id,
        "target_article_id": pin.target_article_id,
        "target_map_id": pin.target_map_id,
        "title": pin.title,
        "x_position": float(pin.x_position),
        "y_position": float(pin.y_position),
        "icon": pin.icon,
        "color": pin.color,
        "visibility": pin.visibility,
        "is_locked": False,
    }


def sanitize_chapter_dict(chapter: ManuscriptChapter, role: UserRole) -> Optional[dict[str, Any]]:
    """
    Aplica as regras de Fog of War para serialização de um Capítulo de Manuscrito.
    """
    if role == UserRole.MESTRE:
        return {
            "id": chapter.id,
            "manuscript_id": chapter.manuscript_id,
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
            "manuscript_id": chapter.manuscript_id,
            "title": chapter.title,
            "content": "",
            "order_index": chapter.order_index,
            "visibility": chapter.visibility,
            "is_locked": True,
        }

    return {
        "id": chapter.id,
        "manuscript_id": chapter.manuscript_id,
        "title": chapter.title,
        "content": chapter.content,
        "order_index": chapter.order_index,
        "visibility": chapter.visibility,
        "is_locked": False,
    }
