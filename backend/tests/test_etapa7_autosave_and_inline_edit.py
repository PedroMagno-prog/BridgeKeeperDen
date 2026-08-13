"""Testes de integração para a Etapa 7: Pastas de Artigos e Conteúdo Markdown Contínuo."""
import uuid
import pytest
from sqlalchemy import select
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import AsyncSessionLocal
from app.db.models.user import User
from app.db.models.world import World
from app.db.models.world_member import WorldMember
from app.db.models.article_folder import ArticleFolder
from app.db.models.enums import UserRole, VisibilityType
from app.core.security import criar_access_token
from app.services import article_service


@pytest.mark.asyncio
async def test_etapa7_folders_and_unified_content_flow():
    suffix = uuid.uuid4().hex[:6]
    async with AsyncSessionLocal() as db:
        mestre = User(username=f"gm_e7_{suffix}", email=f"gm_e7_{suffix}@example.com", password_hash="hash")
        db.add(mestre)
        await db.flush()

        world = World(name="Mundo Etapa 7", owner_id=mestre.id)
        db.add(world)
        await db.flush()

        db.add(WorldMember(world_id=world.id, user_id=mestre.id, role=UserRole.MESTRE))
        await db.commit()

        token_mestre = criar_access_token({"sub": str(mestre.id)})
        headers_mestre = {"Authorization": f"Bearer {token_mestre}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Criar pasta principal
            res_folder = await ac.post(
                f"/api/v1/worlds/{world.id}/articles/folders",
                json={"name": "Grimórios e Magia"},
                headers=headers_mestre,
            )
            assert res_folder.status_code == 201, res_folder.text
            folder_data = res_folder.json()
            folder_id = folder_data["id"]

            # 2. Criar subpasta
            res_subfolder = await ac.post(
                f"/api/v1/worlds/{world.id}/articles/folders",
                json={"name": "Magias de Fogo", "parent_id": folder_id},
                headers=headers_mestre,
            )
            assert res_subfolder.status_code == 201
            subfolder_id = res_subfolder.json()["id"]

            # 3. Criar artigo vinculado à subpasta com texto Markdown unificado
            res_article = await ac.post(
                f"/api/v1/worlds/{world.id}/articles/",
                json={
                    "title": "Grimório do Sol Sagrado",
                    "folder_id": subfolder_id,
                    "content": "# Introdução\n\nTexto inicial do grimório.\n\n# Capítulo 1\n\nO ritual do sol.",
                    "visibility": "TOTAL",
                    "tags": [".magia", ".sol"],
                },
                headers=headers_mestre,
            )
            assert res_article.status_code == 201, res_article.text
            art_data = res_article.json()
            article_id = art_data["id"]
            assert art_data["folder_id"] == subfolder_id
            assert "Texto inicial do grimório" in art_data["content"]

            # 4. Atualizar artigo via PUT (Auto-Save de conteúdo contínuo)
            res_update = await ac.put(
                f"/api/v1/worlds/{world.id}/articles/{article_id}",
                json={
                    "title": "Grimório do Sol Divino",
                    "content": "# Introdução\n\nTexto atualizado pelo auto-save.\n\n# Capítulo 1\n\nNovo ritual do sol.",
                    "tags": [".magia", ".sol", ".divino"],
                },
                headers=headers_mestre,
            )
            assert res_update.status_code == 200
            updated_data = res_update.json()
            assert updated_data["title"] == "Grimório do Sol Divino"
            assert "Texto atualizado pelo auto-save" in updated_data["content"]

            # Cleanup
            await db.delete(world)
            await db.delete(mestre)
            await db.commit()
