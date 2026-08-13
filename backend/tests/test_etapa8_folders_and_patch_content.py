"""Testes de integração para a Etapa 8: CRUD de Pastas, Árvore do Codex e PATCH de Conteúdo."""
import uuid
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
async def test_etapa8_folders_tree_and_patch_content_flow():
    suffix = uuid.uuid4().hex[:6]
    async with AsyncSessionLocal() as db:
        # 1. Criar Usuário Mestre
        mestre = User(username=f"gm_e8_{suffix}", email=f"gm_e8_{suffix}@example.com", password_hash="hash")
        db.add(mestre)
        await db.flush()

        world = World(name="Mundo Etapa 8", owner_id=mestre.id)
        db.add(world)
        await db.flush()

        db.add(WorldMember(world_id=world.id, user_id=mestre.id, role=UserRole.MESTRE))
        await db.commit()

        token_mestre = criar_access_token({"sub": str(mestre.id)})
        headers_mestre = {"Authorization": f"Bearer {token_mestre}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 2. Criar Pasta Raiz
            res_root_folder = await ac.post(
                f"/api/v1/worlds/{world.id}/folders/",
                json={"name": "Geografia"},
                headers=headers_mestre,
            )
            assert res_root_folder.status_code == 201, res_root_folder.text
            root_folder = res_root_folder.json()
            root_folder_id = root_folder["id"]

            # 3. Criar Subpasta
            res_subfolder = await ac.post(
                f"/api/v1/worlds/{world.id}/folders/",
                json={"name": "Cidades", "parent_id": root_folder_id},
                headers=headers_mestre,
            )
            assert res_subfolder.status_code == 201, res_subfolder.text
            subfolder = res_subfolder.json()
            subfolder_id = subfolder["id"]

            # 4. Criar Artigo na Subpasta
            res_art = await ac.post(
                f"/api/v1/worlds/{world.id}/articles/",
                json={
                    "title": "Capital Eldoria",
                    "folder_id": subfolder_id,
                    "content": "# Eldoria\n\nCapital principal do reino.",
                    "visibility": "TOTAL",
                },
                headers=headers_mestre,
            )
            assert res_art.status_code == 201, res_art.text
            art_data = res_art.json()
            article_id = art_data["id"]
            assert art_data["folder_id"] == subfolder_id

            # 5. Criar Artigo na Raiz (sem pasta)
            res_root_art = await ac.post(
                f"/api/v1/worlds/{world.id}/articles/",
                json={
                    "title": "Lore Geral",
                    "content": "# Introdução\n\nHistória antiga do mundo.",
                    "visibility": "TOTAL",
                },
                headers=headers_mestre,
            )
            assert res_root_art.status_code == 201, res_root_art.text

            # 6. Testar GET /folders (Obter árvore de pastas e artigos)
            res_tree = await ac.get(
                f"/api/v1/worlds/{world.id}/folders/",
                headers=headers_mestre,
            )
            assert res_tree.status_code == 200, res_tree.text
            tree_data = res_tree.json()

            # Verificar estrutura da árvore
            assert len(tree_data["folders"]) == 1
            root_f_node = tree_data["folders"][0]
            assert root_f_node["name"] == "Geografia"
            assert len(root_f_node["children"]) == 1

            sub_f_node = root_f_node["children"][0]
            assert sub_f_node["name"] == "Cidades"
            assert len(sub_f_node["articles"]) == 1
            assert sub_f_node["articles"][0]["title"] == "Capital Eldoria"

            # Verificar artigo raiz
            assert len(tree_data["root_articles"]) == 1
            assert tree_data["root_articles"][0]["title"] == "Lore Geral"

            # 7. Testar Rota Otimizada de Autosave: PATCH /articles/{id}/content
            res_patch = await ac.patch(
                f"/api/v1/worlds/{world.id}/articles/{article_id}/content",
                json={"content": "# Eldoria Atualizada\n\nNova descrição com [[Lore Geral]] via autosave."},
                headers=headers_mestre,
            )
            assert res_patch.status_code == 200, res_patch.text
            patched_data = res_patch.json()
            assert "Eldoria Atualizada" in patched_data["content"]

            # Confirmar alteração direta no banco
            db_art = await article_service.buscar_artigo(db, uuid.UUID(article_id), world.id)
            assert "Nova descrição com [[Lore Geral]]" in db_art.content

            # 8. Testar Exclusão de Pasta (DELETE /folders/{id})
            res_del_folder = await ac.delete(
                f"/api/v1/worlds/{world.id}/folders/{subfolder_id}",
                headers=headers_mestre,
            )
            assert res_del_folder.status_code == 204

            # Verificar se o artigo teve seu folder_id redefinido para NULL
            art_after_del = await article_service.buscar_artigo(
                db, uuid.UUID(article_id), world.id, populate_existing=True
            )
            assert art_after_del is not None
            assert art_after_del.folder_id is None

            # Cleanup
            await db.delete(world)
            await db.delete(mestre)
            await db.commit()
