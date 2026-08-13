"""Testes de integracao para a API de Mapas, Layers, Pins Polimorficos e Sub-Mapas."""
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
async def test_maps_and_pins_flow():
    import uuid
    suffix = uuid.uuid4().hex[:6]
    async with AsyncSessionLocal() as db:
        user = User(username=f"map_test_user_{suffix}", email=f"map_test_{suffix}@example.com", password_hash="hash")
        db.add(user)
        await db.flush()

        world = World(name="Mundo Cartografia", owner_id=user.id)
        db.add(world)
        await db.flush()

        member = WorldMember(world_id=world.id, user_id=user.id, role=UserRole.MESTRE)
        db.add(member)
        await db.flush()

        # Artigo de teste para vincular ao pin
        article = Article(world_id=world.id, title="Castelo de Thanatos", visibility=VisibilityType.TOTAL, created_by=user.id)
        db.add(article)
        await db.commit()

        token = criar_access_token({"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Criar Mapa Principal
            res_map1 = await ac.post(
                f"/api/v1/worlds/{world.id}/maps/",
                json={"title": "Continente de Valoria", "image_url": "http://example.com/valoria.webp"},
                headers=headers,
            )
            assert res_map1.status_code == 201, res_map1.text
            map1_id = res_map1.json()["id"]

            # 2. Criar Sub-Mapa
            res_map2 = await ac.post(
                f"/api/v1/worlds/{world.id}/maps/",
                json={"title": "Masmorra de Thanatos", "image_url": "http://example.com/masmorra.webp"},
                headers=headers,
            )
            assert res_map2.status_code == 201, res_map2.text
            map2_id = res_map2.json()["id"]

            # 3. Criar Camada no Mapa 1
            res_layer = await ac.post(
                f"/api/v1/worlds/{world.id}/maps/{map1_id}/layers",
                json={"name": "Locais Importantes", "is_default_active": True},
                headers=headers,
            )
            assert res_layer.status_code == 201, res_layer.text
            layer_id = res_layer.json()["id"]

            # 4. Criar Pin vinculado a Artigo
            res_pin_art = await ac.post(
                f"/api/v1/worlds/{world.id}/maps/{map1_id}/pins",
                json={
                    "title": "Castelo de Thanatos",
                    "x_position": 45.5,
                    "y_position": 60.2,
                    "icon": "castle",
                    "color": "#EAB308",
                    "visibility": "TOTAL",
                    "layer_id": layer_id,
                    "target_article_id": str(article.id),
                },
                headers=headers,
            )
            assert res_pin_art.status_code == 201, res_pin_art.text
            pin_art_data = res_pin_art.json()
            assert pin_art_data["target_article"]["title"] == "Castelo de Thanatos"

            # 5. Criar Pin vinculado a Sub-Mapa
            res_pin_map = await ac.post(
                f"/api/v1/worlds/{world.id}/maps/{map1_id}/pins",
                json={
                    "title": "Entrada da Masmorra",
                    "x_position": 20.0,
                    "y_position": 30.0,
                    "icon": "dungeon",
                    "color": "#EF4444",
                    "visibility": "TOTAL",
                    "target_map_id": map2_id,
                },
                headers=headers,
            )
            assert res_pin_map.status_code == 201, res_pin_map.text
            pin_map_id = res_pin_map.json()["id"]
            assert res_pin_map.json()["target_map_title"] == "Masmorra de Thanatos"

            # 6. Atualizar posicao do pino (drag and drop)
            res_update_pos = await ac.put(
                f"/api/v1/worlds/{world.id}/maps/{map1_id}/pins/{pin_map_id}",
                json={"x_position": 25.0, "y_position": 35.0},
                headers=headers,
            )
            assert res_update_pos.status_code == 200, res_update_pos.text
            assert res_update_pos.json()["x_position"] == 25.0

            # 7. Buscar Detalhes do Mapa
            res_detail = await ac.get(f"/api/v1/worlds/{world.id}/maps/{map1_id}", headers=headers)
            assert res_detail.status_code == 200, res_detail.text
            detail_data = res_detail.json()
            assert len(detail_data["pins"]) == 2

            # Cleanup
            await db.delete(article)
            await db.delete(member)
            await db.delete(world)
            await db.delete(user)
            await db.commit()
