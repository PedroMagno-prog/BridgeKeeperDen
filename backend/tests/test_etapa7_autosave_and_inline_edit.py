"""Testes de integração para a Etapa 7: Auto-Save e Edição Inline."""
import io
import uuid
import pytest
from sqlalchemy import select
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
async def test_etapa7_autosave_and_section_id_preservation():
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

        # 1. Criar artigo inicial
        article = await article_service.criar_artigo(
            db,
            world.id,
            mestre.id,
            UserRole.MESTRE,
            title="Grimório do Sol",
            visibility=VisibilityType.TOTAL,
            in_game_date="1000",
            in_game_sort_order=1,
            tags=[".magia", ".sol"],
            sections=[
                {"title": "Introdução", "content": "Texto inicial."},
                {"title": "Capítulo 1", "content": "O ritual do sol."},
            ],
        )
        await db.commit()

        from app.db.models.article_section import ArticleSection
        sec_res = await db.execute(
            select(ArticleSection).where(ArticleSection.article_id == article.id).order_by(ArticleSection.order_index)
        )
        sections_before = sec_res.scalars().all()
        sec1_id = str(sections_before[0].id)
        sec2_id = str(sections_before[1].id)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 2. Simular Auto-Save via PUT atualizando título e conteúdo da Seção 1 passando seus IDs
            res_autosave = await ac.put(
                f"/api/v1/worlds/{world.id}/articles/{article.id}",
                json={
                    "title": "Grimório do Sol Sagrado",
                    "tags": [".magia", ".sol", ".sagrado"],
                    "sections": [
                        {"id": sec1_id, "title": "Introdução Editada", "content": "Texto atualizado pelo auto-save com [[Outro Artigo]].", "order_index": 0},
                        {"id": sec2_id, "title": "Capítulo 1", "content": "O ritual do sol atualizado.", "order_index": 1},
                    ],
                },
                headers=headers_mestre,
            )
            assert res_autosave.status_code == 200, res_autosave.text
            data = res_autosave.json()

            assert data["title"] == "Grimório do Sol Sagrado"
            assert len(data["sections"]) == 2
            assert data["sections"][0]["id"] == sec1_id, "ID da Seção 1 deve ser preservado!"
            assert data["sections"][0]["title"] == "Introdução Editada"
            assert data["sections"][1]["id"] == sec2_id, "ID da Seção 2 deve ser preservado!"

            # Cleanup
            await db.delete(world)
            await db.delete(mestre)
            await db.commit()
