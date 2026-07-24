from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.auth import get_current_user
from app.db.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.services import auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Cria uma nova conta de usuário."""
    return await auth_service.register_user(db, data)


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Autentica o usuário e retorna o token JWT."""
    return await auth_service.authenticate_user(db, data)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Obtém os dados do usuário logado."""
    return user
