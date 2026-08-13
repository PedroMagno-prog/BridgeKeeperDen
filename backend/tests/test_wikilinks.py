"""Testes de integracao para o sistema de Wikilinks, Autocomplete e Backlinks."""
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
async def test_wikilinks_and_backlinks_flow():
    async with AsyncSessionLocal() as db:
        # 1. Criar usuario e mundo
        user = User(username="wiki_test_user", email="wiki_test@example.com", password_hash="hash")
        db.add(user)
        await db.flush()

        world = World(name="Mundo Wikilinks", owner_id=user.id)
        db.add(world)
        await db.flush()

        member = WorldMember(world_id=world.id, user_id=user.id, role=UserRole.MESTRE)
        db.add(member)
        await db.flush()

        # 2. Criar dois artigos
        art_target = Article(world_id=world.id, title="Cidade de Thanatos", visibility=VisibilityType.TOTAL, created_by=user.id)
        art_source = Article(
            world_id=world.id,
            title="Rei Eldrin",
            content="# História\n\nEle é o governante lendário da [[Cidade de Thanatos]] desde tempos imemoriais.",
            visibility=VisibilityType.TOTAL,
            created_by=user.id,
        )
        db.add(art_target)
        db.add(art_source)
        await db.commit()

        token = criar_access_token({"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 3. Testar GET /resolve (existente)
            res_resolve_exists = await ac.get(
                f"/api/v1/worlds/{world.id}/articles/resolve",
                params={"title": "Cidade de Thanatos"},
                headers=headers,
            )
            assert res_resolve_exists.status_code == 200, res_resolve_exists.text
            data_resolve = res_resolve_exists.json()
            assert data_resolve["exists"] is True
            assert data_resolve["article_id"] == str(art_target.id)

            # 4. Testar GET /resolve (inexistente)
            res_resolve_fake = await ac.get(
                f"/api/v1/worlds/{world.id}/articles/resolve",
                params={"title": "Local Inexistente"},
                headers=headers,
            )
            assert res_resolve_fake.status_code == 200, res_resolve_fake.text
            assert res_resolve_fake.json()["exists"] is False

            # 5. Testar GET /search-mentions (autocomplete)
            res_mentions = await ac.get(
                f"/api/v1/worlds/{world.id}/articles/search-mentions",
                params={"query": "Thanatos"},
                headers=headers,
            )
            assert res_mentions.status_code == 200, res_mentions.text
            suggestions = res_mentions.json()
            assert len(suggestions) == 1
            assert suggestions[0]["title"] == "Cidade de Thanatos"

            # 6. Testar GET /{article_id}/backlinks
            res_backlinks = await ac.get(
                f"/api/v1/worlds/{world.id}/articles/{art_target.id}/backlinks",
                headers=headers,
            )
            assert res_backlinks.status_code == 200, res_backlinks.text
            backlinks = res_backlinks.json()
            assert len(backlinks) == 1
            assert backlinks[0]["article_id"] == str(art_source.id)
            assert backlinks[0]["title"] == "Rei Eldrin"
            assert "Cidade de Thanatos" in backlinks[0]["snippet"]

            # Cleanup
            await db.delete(art_target)
            await db.delete(art_source)
            await db.delete(member)
            await db.delete(world)
            await db.delete(user)
            await db.commit()
