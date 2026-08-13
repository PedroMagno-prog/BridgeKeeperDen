"""Configurações globais de fixtures do Pytest."""
import pytest
import pytest_asyncio
from app.db.session import engine


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db_engine():
    """Descarta conexões antigas do pool do SQLAlchemy antes de cada teste para evitar reuso entre event loops."""
    await engine.dispose()
    yield
    await engine.dispose()
