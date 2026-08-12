"""Rota para o Módulo Graph View (Visualizador em Grafo de Conexões)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.world_access import WorldContext, get_world_ctx
from app.schemas.graph import WorldGraphOut
from app.services import graph_service

router = APIRouter()


@router.get("/", response_model=WorldGraphOut, summary="Obtém o grafo de conexões do mundo")
async def obter_grafo_do_mundo(
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """
    Retorna a lista de nós e arestas de conexões (Wikilinks, vínculos diretos)
    do mundo atual sanitizada pela Névoa de Guerra.
    """
    return await graph_service.gerar_grafo_do_mundo(db, ctx.world_id, ctx.role)
