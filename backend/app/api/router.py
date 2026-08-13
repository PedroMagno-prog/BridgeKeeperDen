from fastapi import APIRouter

from app.api.routes import auth, users, worlds, articles, folders, maps, timeline, manuscripts, inventories, quests, graph

api_router = APIRouter()

# ── Auth & Users ──────────────────────────────────────────────────────────────
api_router.include_router(auth.router,   prefix="/auth",   tags=["Auth"])
api_router.include_router(users.router,  prefix="/users",  tags=["Users"])

# ── Worlds ────────────────────────────────────────────────────────────────────
api_router.include_router(worlds.router, prefix="/worlds", tags=["Worlds"])

# ── Conteudo (scoped by world_id) ─────────────────────────────────────────────
api_router.include_router(
    folders.router,
    prefix="/worlds/{world_id}/folders",
    tags=["Folders"],
)
api_router.include_router(
    articles.router,
    prefix="/worlds/{world_id}/articles",
    tags=["Articles"],
)
api_router.include_router(
    maps.router,
    prefix="/worlds/{world_id}/maps",
    tags=["Maps"],
)
api_router.include_router(
    timeline.router,
    prefix="/worlds/{world_id}/timeline",
    tags=["Timeline"],
)
api_router.include_router(
    manuscripts.router,
    prefix="/worlds/{world_id}/manuscripts",
    tags=["Manuscripts"],
)
api_router.include_router(
    inventories.router,
    prefix="/worlds/{world_id}/inventories",
    tags=["Inventories"],
)
api_router.include_router(
    quests.router,
    prefix="/worlds/{world_id}/quests",
    tags=["Quests"],
)
api_router.include_router(
    graph.router,
    prefix="/worlds/{world_id}/graph",
    tags=["Graph"],
)
