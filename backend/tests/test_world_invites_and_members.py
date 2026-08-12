"""Testes de integração para o módulo de Convites e Gestão de Membros do Mundo (Etapa 4)."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import AsyncSessionLocal
from app.db.models.user import User
from app.db.models.world import World
from app.db.models.world_member import WorldMember
from app.db.models.enums import UserRole
from app.core.security import criar_access_token


@pytest.mark.asyncio
async def test_world_invites_and_members_flow():
    import uuid
    suffix = uuid.uuid4().hex[:6]
    async with AsyncSessionLocal() as db:
        # 1. Criar Usuário A (Mestre) e Usuário B (Jogador)
        user_a = User(username=f"mestre_{suffix}", email=f"mestre_{suffix}@example.com", password_hash="hash")
        user_b = User(username=f"jogador_{suffix}", email=f"jogador_{suffix}@example.com", password_hash="hash")
        db.add_all([user_a, user_b])
        await db.flush()

        # 2. Criar Mundo do Mestre (Usuário A)
        world = World(name="Mundo dos Convites", owner_id=user_a.id)
        db.add(world)
        await db.flush()

        member_a = WorldMember(world_id=world.id, user_id=user_a.id, role=UserRole.MESTRE)
        db.add(member_a)
        await db.commit()

        token_a = criar_access_token({"sub": str(user_a.id)})
        headers_a = {"Authorization": f"Bearer {token_a}"}

        token_b = criar_access_token({"sub": str(user_b.id)})
        headers_b = {"Authorization": f"Bearer {token_b}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 3. Testar Obter Info de Convite pelo Usuário B
            res_info = await ac.get(f"/api/v1/worlds/invite-info/{world.invite_code}", headers=headers_b)
            print("RES_INFO STATUS:", res_info.status_code, res_info.text)
            assert res_info.status_code == 200, res_info.text
            info_data = res_info.json()
            assert info_data["world_name"] == "Mundo dos Convites"
            assert info_data["owner_username"] == f"mestre_{suffix}"

            # 4. Usuário B entra no mundo via invite_code
            res_join = await ac.post(f"/api/v1/worlds/join/{world.invite_code}", headers=headers_b)
            print("RES_JOIN STATUS:", res_join.status_code, res_join.text)
            assert res_join.status_code == 200, res_join.text
            joined_world = res_join.json()
            assert joined_world["role"] == "JOGADOR"

            # 5. Tentativa duplicada de entrada pelo Usuário B -> Retorna 400
            res_join_dup = await ac.post(f"/api/v1/worlds/join/{world.invite_code}", headers=headers_b)
            assert res_join_dup.status_code == 400, res_join_dup.text

            # 6. Listar Membros do Mundo
            res_members = await ac.get(f"/api/v1/worlds/{world.id}/members", headers=headers_a)
            assert res_members.status_code == 200, res_members.text
            members_list = res_members.json()
            assert len(members_list) == 2

            # 7. Mestre altera papel do Usuário B para MESTRE
            res_role = await ac.put(
                f"/api/v1/worlds/{world.id}/members/{user_b.id}/role",
                json={"role": "MESTRE"},
                headers=headers_a,
            )
            assert res_role.status_code == 200, res_role.text
            assert res_role.json()["role"] == "MESTRE"

            # 8. Mestre rotaciona código de convite
            old_code = world.invite_code
            res_rotate = await ac.post(f"/api/v1/worlds/{world.id}/rotate-invite", headers=headers_a)
            assert res_rotate.status_code == 200, res_rotate.text
            new_code = res_rotate.json()["invite_code"]
            assert new_code != old_code

            # 9. Código antigo deve retornar 404 agora
            res_old_info = await ac.get(f"/api/v1/worlds/invite-info/{old_code}", headers=headers_b)
            assert res_old_info.status_code == 404

            # 10. Testar que criador (User A) não pode ser removido
            res_del_owner = await ac.delete(f"/api/v1/worlds/{world.id}/members/{user_a.id}", headers=headers_a)
            assert res_del_owner.status_code == 400, res_del_owner.text

            # Cleanup
            await db.delete(world)
            await db.delete(user_a)
            await db.delete(user_b)
            await db.commit()
