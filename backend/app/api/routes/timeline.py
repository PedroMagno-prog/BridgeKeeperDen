import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.auth import get_world_role
from app.db.models.enums import UserRole
from app.schemas.timeline import TimelineResponse
from app.services import timeline_service

router = APIRouter()


@router.get("", response_model=TimelineResponse)
async def get_timeline(
    world_id: uuid.UUID,
    role: UserRole = Depends(get_world_role),
    db: AsyncSession = Depends(get_db),
):
    """Retorna os eventos da linha do tempo e eras agrupados cronologicamente."""
    return await timeline_service.get_timeline(db, world_id, role)
