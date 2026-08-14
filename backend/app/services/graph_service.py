"""Serviço de compilação do Grafo de Conexões do Mundo (Graph View)."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.enums import UserRole, VisibilityType
from app.db.models.article import Article
from app.db.models.quest import Quest
from app.db.models.map import Map
from app.db.models.map_pin import MapPin
from app.db.models.manuscript import Manuscript
from app.schemas.graph import GraphNode, GraphEdge, WorldGraphOut
from app.services.article_service import extract_wikilinks


async def gerar_grafo_do_mundo(
    db: AsyncSession,
    world_id: uuid.UUID,
    role: UserRole,
) -> WorldGraphOut:
    """
    Compila a teia de nós e arestas acessíveis ao usuário no mundo.
    Varre citações de Wikilinks [[Artigo]] e vínculos diretos.
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    # Mapa auxiliar de title.lower() -> node_id
    title_to_node_id: dict[str, str] = {}
    registered_edge_ids: set[str] = set()

    # 1. Carregar Artigos
    stmt_art = (
        select(Article)
        .options(selectinload(Article.tags))
        .where(Article.world_id == world_id)
    )
    if role == UserRole.JOGADOR:
        stmt_art = stmt_art.where(Article.visibility != VisibilityType.NULA)
    art_result = await db.execute(stmt_art)
    articles = art_result.scalars().all()

    for art in articles:
        node_id = f"article:{art.id}"
        is_locked = role == UserRole.JOGADOR and art.visibility == VisibilityType.PARCIAL
        tag_str = art.tags[0].name if art.tags else None
        nodes.append(
            GraphNode(
                id=node_id,
                label=art.title,
                type="ARTICLE",
                category=tag_str,
                folder_id=art.folder_id,
                visibility=art.visibility,
                is_locked=is_locked,
            )
        )
        title_to_node_id[art.title.strip().lower()] = node_id

    # 2. Carregar Quests
    stmt_quest = (
        select(Quest)
        .options(selectinload(Quest.objectives))
        .where(Quest.world_id == world_id)
    )
    if role == UserRole.JOGADOR:
        stmt_quest = stmt_quest.where(Quest.visibility != VisibilityType.NULA)
    quest_result = await db.execute(stmt_quest)
    quests = quest_result.scalars().all()

    for q in quests:
        node_id = f"quest:{q.id}"
        is_locked = role == UserRole.JOGADOR and q.visibility == VisibilityType.PARCIAL
        nodes.append(
            GraphNode(
                id=node_id,
                label=q.title,
                type="QUEST",
                category=q.category.value,
                visibility=q.visibility,
                is_locked=is_locked,
            )
        )
        title_to_node_id[q.title.strip().lower()] = node_id

        # Vínculo direto de Quest -> Article (se houver)
        if q.article_id:
            target_node_id = f"article:{q.article_id}"
            edge_id = f"{node_id}->{target_node_id}"
            if edge_id not in registered_edge_ids:
                registered_edge_ids.add(edge_id)
                edges.append(GraphEdge(id=edge_id, source=node_id, target=target_node_id, label="Vinculado"))

    # 3. Carregar Mapas e Marcadores
    stmt_maps = (
        select(Map)
        .options(selectinload(Map.pins))
        .where(Map.world_id == world_id)
    )
    map_result = await db.execute(stmt_maps)
    maps = map_result.scalars().all()

    for m in maps:
        map_node_id = f"map:{m.id}"
        nodes.append(
            GraphNode(
                id=map_node_id,
                label=m.title,
                type="MAP",
                visibility=VisibilityType.TOTAL,
                is_locked=False,
            )
        )
        title_to_node_id[m.title.strip().lower()] = map_node_id

        for pin in m.pins:
            if role == UserRole.JOGADOR and pin.visibility == VisibilityType.NULA:
                continue
            pin_node_id = f"pin:{pin.id}"
            is_locked = role == UserRole.JOGADOR and pin.visibility == VisibilityType.PARCIAL
            nodes.append(
                GraphNode(
                    id=pin_node_id,
                    label=pin.title,
                    type="PIN",
                    category=pin.icon,
                    visibility=pin.visibility,
                    is_locked=is_locked,
                )
            )
            # Pino pertence ao Mapa
            edge_id = f"{map_node_id}->{pin_node_id}"
            if edge_id not in registered_edge_ids:
                registered_edge_ids.add(edge_id)
                edges.append(GraphEdge(id=edge_id, source=map_node_id, target=pin_node_id, label="Contém"))

            # Pino -> Artigo
            if pin.target_article_id and not is_locked:
                target_node_id = f"article:{pin.target_article_id}"
                edge_id = f"{pin_node_id}->{target_node_id}"
                if edge_id not in registered_edge_ids:
                    registered_edge_ids.add(edge_id)
                    edges.append(GraphEdge(id=edge_id, source=pin_node_id, target=target_node_id, label="Lore"))

            # Pino -> Sub-Mapa
            if pin.target_map_id and not is_locked:
                target_node_id = f"map:{pin.target_map_id}"
                edge_id = f"{pin_node_id}->{target_node_id}"
                if edge_id not in registered_edge_ids:
                    registered_edge_ids.add(edge_id)
                    edges.append(GraphEdge(id=edge_id, source=pin_node_id, target=target_node_id, label="Sub-Mapa"))

    # 4. Extrair Wikilinks [[Artigo]] do Conteúdo de Artigos e Descrições de Quests
    for art in articles:
        if role == UserRole.JOGADOR and art.visibility == VisibilityType.PARCIAL:
            continue
        source_id = f"article:{art.id}"
        wikilinks = extract_wikilinks(art.content or "")
        for target_title, _ in wikilinks:
            target_node_id = title_to_node_id.get(target_title.lower())
            if target_node_id and target_node_id != source_id:
                edge_id = f"{source_id}->{target_node_id}"
                if edge_id not in registered_edge_ids:
                    registered_edge_ids.add(edge_id)
                    edges.append(GraphEdge(id=edge_id, source=source_id, target=target_node_id, label="Cita"))

    for q in quests:
        if role == UserRole.JOGADOR and q.visibility == VisibilityType.PARCIAL:
            continue
        source_id = f"quest:{q.id}"
        full_text = f"{q.description} {q.rewards or ''}"
        wikilinks = extract_wikilinks(full_text)
        for target_title, _ in wikilinks:
            target_node_id = title_to_node_id.get(target_title.lower())
            if target_node_id and target_node_id != source_id:
                edge_id = f"{source_id}->{target_node_id}"
                if edge_id not in registered_edge_ids:
                    registered_edge_ids.add(edge_id)
                    edges.append(GraphEdge(id=edge_id, source=source_id, target=target_node_id, label="Menciona"))

    return WorldGraphOut(nodes=nodes, edges=edges)
