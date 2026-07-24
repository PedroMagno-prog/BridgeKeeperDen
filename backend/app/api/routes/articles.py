import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.auth import get_current_user, get_world_role
from app.db.models.user import User
from app.db.models.enums import UserRole
from app.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    CharacterInventoryCreate,
    CharacterInventoryResponse,
)
from app.services import article_service

router = APIRouter()


@router.get("", response_model=List[ArticleResponse])
async def list_articles(
    world_id: uuid.UUID,
    tag: Optional[str] = Query(None, description="Filtrar por nome de tag (ex: .Facção)"),
    search: Optional[str] = Query(None, description="Busca por título"),
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Lista os artigos de um mundo com suporte a filtros e Fog of War."""
    return await article_service.list_articles(db, world_id, role, tag, search)


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    world_id: uuid.UUID,
    data: ArticleCreate,
    user: User = Depends(get_current_user),
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo artigo (Default Mestre = NULA, Default Jogador = TOTAL)."""
    return await article_service.create_article(db, world_id, user, role, data)


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    world_id: uuid.UUID,
    article_id: uuid.UUID,
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Obtém o detalhe de um artigo específico com Fog of War."""
    return await article_service.get_article_detail(db, world_id, article_id, role)


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    world_id: uuid.UUID,
    article_id: uuid.UUID,
    data: ArticleUpdate,
    user: User = Depends(get_current_user),
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza um artigo."""
    return await article_service.update_article(db, world_id, article_id, user, role, data)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    world_id: uuid.UUID,
    article_id: uuid.UUID,
    user: User = Depends(get_current_user),
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Remove um artigo."""
    await article_service.delete_article(db, world_id, article_id, user, role)


@router.post("/{article_id}/inventory", response_model=CharacterInventoryResponse, status_code=status.HTTP_201_CREATED)
async def add_inventory(
    world_id: uuid.UUID,
    article_id: uuid.UUID,
    data: CharacterInventoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Adiciona item na mochila/inventário de um artigo de personagem."""
    return await article_service.add_inventory_item(db, world_id, article_id, data)
