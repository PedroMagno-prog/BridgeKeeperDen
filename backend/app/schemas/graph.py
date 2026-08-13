"""Schemas Pydantic para o Grafo de Conexões (Graph View)."""
from __future__ import annotations

from pydantic import BaseModel
from app.db.models.enums import VisibilityType


class GraphNode(BaseModel):
    """Nó no grafo de conexões (Artigo, Quest, Mapa, Pino)."""
    id: str
    label: str
    type: str  # "ARTICLE" | "QUEST" | "MAP" | "PIN" | "CHAPTER"
    category: str | None = None
    folder_id: int | None = None
    visibility: VisibilityType
    is_locked: bool = False


class GraphEdge(BaseModel):
    """Aresta direcionada de citação entre dois nós."""
    id: str
    source: str
    target: str
    label: str | None = None


class WorldGraphOut(BaseModel):
    """Grafo de conexões completo do mundo."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]
