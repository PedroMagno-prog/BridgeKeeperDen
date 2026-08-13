"""Testes de integração para a Etapa 6: Permissões Granulares, CONTROLADO e Artigos."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import AsyncSessionLocal
from app.db.models.user import User
from app.db.models.world import World
from app.db.models.world_member import WorldMember
from app.db.models.enums import UserRole, VisibilityType
from app.core.security import criar_access_token
from app.services import article_service


@pytest.mark.asyncio
async def test_etapa6_permissions_and_image_flow():
    import uuid
    suffix = uuid.uuid4().hex[:6]
    async with AsyncSessionLocal() as db:
        # 1. Criar Mestre, Jogador A e Jogador B
        mestre = User(username=f"gm_e6_{suffix}", email=f"gm_e6_{suffix}@example.com", password_hash="hash")
        player_a = User(username=f"pla_e6_{suffix}", email=f"pla_e6_{suffix}@example.com", password_hash="hash")
        player_b = User(username=f"plb_e6_{suffix}", email=f"plb_e6_{suffix}@example.com", password_hash="hash")
        db.add_all([mestre, player_a, player_b])
        await db.flush()

        world = World(name="Mundo Etapa 6", owner_id=mestre.id)
        db.add(world)
        await db.flush()

        db.add(WorldMember(world_id=world.id, user_id=mestre.id, role=UserRole.MESTRE))
        db.add(WorldMember(world_id=world.id, user_id=player_a.id, role=UserRole.JOGADOR))
        db.add(WorldMember(world_id=world.id, user_id=player_b.id, role=UserRole.JOGADOR))
        await db.commit()

        token_mestre = criar_access_token({"sub": str(mestre.id)})
        token_a = criar_access_token({"sub": str(player_a.id)})
        token_b = criar_access_token({"sub": str(player_b.id)})

        headers_mestre = {"Authorization": f"Bearer {token_mestre}"}
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 2. Mestre cria artigo com Visibilidade NULA por padrão
        article = await article_service.criar_artigo(
            db,
            world.id,
            mestre.id,
            UserRole.MESTRE,
            title="Grimório Proibido",
            content="# Visão Geral\n\nSegredos antigos do reino.",
            visibility=VisibilityType.NULA,
            in_game_date="1200",
            in_game_sort_order=1,
            tags=[".magia"],
        )
        await db.commit()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 3. Jogador A e B tentam acessar -> 404 (visibilidade NULA)
            res_a_null = await ac.get(f"/api/v1/worlds/{world.id}/articles/{article.id}", headers=headers_a)
            assert res_a_null.status_code == 404, f"Passo 3a falhou: {res_a_null.status_code}"

            res_b_null = await ac.get(f"/api/v1/worlds/{world.id}/articles/{article.id}", headers=headers_b)
            assert res_b_null.status_code == 404, f"Passo 3b falhou: {res_b_null.status_code}"

            # 4. Mestre configura permissão granular: Jogador A = CONTROLADO, Jogador B = NULA
            res_perm_set = await ac.put(
                f"/api/v1/worlds/{world.id}/articles/{article.id}/permissions",
                json={
                    "permissions": [
                        {"user_id": str(player_a.id), "visibility": "CONTROLADO"},
                        {"user_id": str(player_b.id), "visibility": "NULA"},
                    ]
                },
                headers=headers_mestre,
            )
            assert res_perm_set.status_code == 200, f"Passo 4 falhou: {res_perm_set.status_code} - {res_perm_set.text}"

            # 5. Jogador A faz GET -> Lê conteúdo completo com can_edit=False e can_delete=False
            res_a_read = await ac.get(f"/api/v1/worlds/{world.id}/articles/{article.id}", headers=headers_a)
            assert res_a_read.status_code == 200, f"Passo 5a falhou: {res_a_read.status_code} - {res_a_read.text}"
            detail_a = res_a_read.json()
            assert detail_a["title"] == "Grimório Proibido"
            assert detail_a["can_edit"] is False
            assert detail_a["can_delete"] is False

            # Jogador B continua recebendo 404 (NULA)
            res_b_read = await ac.get(f"/api/v1/worlds/{world.id}/articles/{article.id}", headers=headers_b)
            assert res_b_read.status_code == 404, f"Passo 5e falhou: {res_b_read.status_code}"

            # 6. Jogador A tenta PUT e DELETE -> Recebe 403 Forbidden
            res_a_put = await ac.put(
                f"/api/v1/worlds/{world.id}/articles/{article.id}",
                json={"title": "Hackeado pelo Jogador A"},
                headers=headers_a,
            )
            assert res_a_put.status_code == 403, f"Passo 6a falhou: {res_a_put.status_code} - {res_a_put.text}"

            res_a_del = await ac.delete(f"/api/v1/worlds/{world.id}/articles/{article.id}", headers=headers_a)
            assert res_a_del.status_code == 403, f"Passo 6b falhou: {res_a_del.status_code} - {res_a_del.text}"

            # Cleanup
            await db.delete(world)
            await db.delete(mestre)
            await db.delete(player_a)
            await db.delete(player_b)
            await db.commit()
