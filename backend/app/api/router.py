from fastapi import APIRouter

from app.api.routes import auth, worlds, articles, maps, timeline, manuscripts

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(worlds.router, prefix="/worlds", tags=["Mundos"])
api_router.include_router(
    articles.router, prefix="/worlds/{world_id}/articles", tags=["Artigos (Codex)"]
)
api_router.include_router(
    maps.router, prefix="/worlds/{world_id}/maps", tags=["Mapas Interativos"]
)
api_router.include_router(
    timeline.router, prefix="/worlds/{world_id}/timeline", tags=["Linha do Tempo"]
)
api_router.include_router(
    manuscripts.router, prefix="/worlds/{world_id}/manuscripts", tags=["Manuscritos"]
)
