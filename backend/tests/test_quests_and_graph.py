"""Testes de integração para o módulo de Quests e Graph View."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import AsyncSessionLocal
from app.db.models.user import User
from app.db.models.world import World
from app.db.models.world_member import WorldMember
from app.db.models.article import Article
from app.db.models.enums import UserRole, VisibilityType
from app.core.security import criar_access_token


@pytest.mark.asyncio
async def test_quests_and_graph_flow():
    async with AsyncSessionLocal() as db:
        user = User(username="quest_test_user", email="quest_test@example.com", password_hash="hash")
        db.add(user)
        await db.flush()

        world = World(name="Mundo Quests e Grafo", owner_id=user.id)
        db.add(world)
        await db.flush()

        member = WorldMember(world_id=world.id, user_id=user.id, role=UserRole.MESTRE)
        db.add(member)
        await db.flush()

        article = Article(world_id=world.id, title="Forja dos Titãs", visibility=VisibilityType.TOTAL, created_by=user.id)
        db.add(article)
        await db.commit()

        token = criar_access_token({"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Criar Quest com Objetivos
            res_create = await ac.post(
                f"/api/v1/worlds/{world.id}/quests/",
                json={
                    "title": "Em Busca da Forja",
                    "description": "Explorar o local lendário [[Forja dos Titãs]].",
                    "category": "MAIN_QUEST",
                    "status": "IN_PROGRESS",
                    "visibility": "TOTAL",
                    "rewards": "500 PO e Artefato Raro",
                    "article_id": str(article.id),
                    "objectives": [
                        {"description": "Encontrar a entrada", "is_completed": True, "order_index": 0},
                        {"description": "Derrotar o Guardião", "is_completed": False, "order_index": 1},
                    ],
                },
                headers=headers,
            )
            assert res_create.status_code == 201, res_create.text
            quest_data = res_create.json()
            assert quest_data["title"] == "Em Busca da Forja"
            assert len(quest_data["objectives"]) == 2
            quest_id = quest_data["id"]
            obj_id = quest_data["objectives"][1]["id"]

            # 2. Toggle do segundo objetivo
            res_toggle = await ac.patch(
                f"/api/v1/worlds/{world.id}/quests/{quest_id}/objectives/{obj_id}/toggle",
                headers=headers,
            )
            assert res_toggle.status_code == 200, res_toggle.text
            assert res_toggle.json()["is_completed"] is True

            # 3. Listar Quests
            res_list = await ac.get(f"/api/v1/worlds/{world.id}/quests/", headers=headers)
            assert res_list.status_code == 200, res_list.text
            assert len(res_list.json()) == 1

            # 4. Obter Grafo de Conexões do Mundo
            res_graph = await ac.get(f"/api/v1/worlds/{world.id}/graph/", headers=headers)
            assert res_graph.status_code == 200, res_graph.text
            graph_data = res_graph.json()
            assert len(graph_data["nodes"]) >= 2  # Article + Quest
            assert len(graph_data["edges"]) >= 1  # Citação Wikilink ou vínculo direto

            # Cleanup
            await db.delete(article)
            await db.delete(member)
            await db.delete(world)
            await db.delete(user)
            await db.commit()
