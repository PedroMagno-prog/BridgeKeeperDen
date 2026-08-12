"""Testes de integracao para a API de Inventarios e Grupos."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import AsyncSessionLocal
from app.db.models.user import User
from app.db.models.world import World
from app.db.models.world_member import WorldMember
from app.db.models.enums import UserRole, VisibilityType
from app.core.security import criar_access_token


@pytest.mark.asyncio
async def test_inventories_api_flow():
    async with AsyncSessionLocal() as db:
        # 1. Criar usuario de teste
        user = User(username="test_inv_user", email="test_inv@example.com", password_hash="hash")
        db.add(user)
        await db.flush()

        # 2. Criar mundo de teste
        world = World(name="Mundo Teste Inventario", owner_id=user.id)
        db.add(world)
        await db.flush()

        # 3. Adicionar membro mestre
        member = WorldMember(world_id=world.id, user_id=user.id, role=UserRole.MESTRE)
        db.add(member)
        await db.commit()

        token = criar_access_token({"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 4. Criar Grupo de Inventario
            res_group = await ac.post(
                f"/api/v1/worlds/{world.id}/inventories/groups",
                json={"name": "Grupo Lojas", "description": "Lojas da Cidade"},
                headers=headers,
            )
            assert res_group.status_code == 201, res_group.text
            group_data = res_group.json()
            assert group_data["name"] == "Grupo Lojas"
            group_id = group_data["id"]

            # 5. Criar Inventario no Grupo
            res_inv = await ac.post(
                f"/api/v1/worlds/{world.id}/inventories/",
                json={"name": "Armaria do Ferreiro", "group_id": group_id, "limit": 5},
                headers=headers,
            )
            assert res_inv.status_code == 201, res_inv.text
            inv_data = res_inv.json()
            assert inv_data["name"] == "Armaria do Ferreiro"
            assert inv_data["group_id"] == group_id
            inv_id = inv_data["id"]

            # 6. Adicionar Item ao Inventario
            res_item = await ac.post(
                f"/api/v1/worlds/{world.id}/inventories/{inv_id}/items",
                json={"custom_name": "Espada de Ferro", "quantity": 2, "notes": "Afiada"},
                headers=headers,
            )
            assert res_item.status_code == 201, res_item.text
            item_data = res_item.json()
            assert item_data["display_name"] == "Espada de Ferro"
            assert item_data["quantity"] == 2

            # 7. Listar Grupos
            res_list = await ac.get(f"/api/v1/worlds/{world.id}/inventories/groups", headers=headers)
            assert res_list.status_code == 200, res_list.text
            groups_list = res_list.json()
            assert len(groups_list) >= 1

            # Cleanup
            await db.delete(member)
            await db.delete(world)
            await db.delete(user)
            await db.commit()
