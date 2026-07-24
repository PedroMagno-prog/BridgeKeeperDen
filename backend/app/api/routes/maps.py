import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.auth import get_current_user, get_world_role
from app.db.models.enums import UserRole
from app.schemas.map import MapCreate, MapResponse, MapPinCreate, MapPinUpdate, MapPinResponse
from app.services import map_service

router = APIRouter()


@router.get("", response_model=List[MapResponse])
async def list_maps(
    world_id: uuid.UUID,
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Lista os mapas do mundo."""
    return await map_service.list_maps(db, world_id)


@router.post("", response_model=MapResponse, status_code=status.HTTP_201_CREATED)
async def create_map(
    world_id: uuid.UUID,
    data: MapCreate,
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Cadastra um novo mapa."""
    return await map_service.create_map(db, world_id, data)


@router.get("/{map_id}", response_model=MapResponse)
async def get_map(
    world_id: uuid.UUID,
    map_id: uuid.UUID,
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Obtém os dados do mapa e seus marcadores sanitizados conforme Fog of War."""
    return await map_service.get_map_detail(db, world_id, map_id, role)


@router.post("/{map_id}/pins", response_model=MapPinResponse, status_code=status.HTTP_201_CREATED)
async def create_pin(
    world_id: uuid.UUID,
    map_id: uuid.UUID,
    data: MapPinCreate,
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Cria um marcador (pin) no mapa."""
    return await map_service.create_pin(db, world_id, map_id, role, data)


@router.put("/{map_id}/pins/{pin_id}", response_model=MapPinResponse)
async def update_pin(
    world_id: uuid.UUID,
    map_id: uuid.UUID,
    pin_id: uuid.UUID,
    data: MapPinUpdate,
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza a posição ou atributos de um marcador."""
    return await map_service.update_pin(db, world_id, map_id, pin_id, role, data)
