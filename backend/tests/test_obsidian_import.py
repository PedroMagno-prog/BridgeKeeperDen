"""Testes de integração para a Importação de Cofres Obsidian (.zip) — Etapa 5."""
import io
import zipfile
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
async def test_obsidian_import_flow():
    import uuid
    suffix = uuid.uuid4().hex[:6]
    async with AsyncSessionLocal() as db:
        # 1. Criar Usuário Mestre e Usuário Jogador
        mestre = User(username=f"gm_obs_{suffix}", email=f"gm_obs_{suffix}@example.com", password_hash="hash")
        jogador = User(username=f"player_obs_{suffix}", email=f"player_obs_{suffix}@example.com", password_hash="hash")
        db.add_all([mestre, jogador])
        await db.flush()

        world = World(name="Mundo Obsidian", owner_id=mestre.id)
        db.add(world)
        await db.flush()

        db.add(WorldMember(world_id=world.id, user_id=mestre.id, role=UserRole.MESTRE))
        db.add(WorldMember(world_id=world.id, user_id=jogador.id, role=UserRole.JOGADOR))
        await db.commit()

        token_mestre = criar_access_token({"sub": str(mestre.id)})
        headers_mestre = {"Authorization": f"Bearer {token_mestre}"}

        token_jogador = criar_access_token({"sub": str(jogador.id)})
        headers_jogador = {"Authorization": f"Bearer {token_jogador}"}

        # 2. Criar Buffer ZIP em memória com notas do Obsidian
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(
                "NotaPrincipal.md",
                "# Visão Geral\nTexto inicial com [[Barão de Eldoria]].\n## História Secreta\nO barão é um vampiro.",
            )
            z.writestr(
                "Regiões/Cataratas.md",
                "---\nin_game_date: 1492-10-12\ntags:\n  - natureza\n  - perigo\n---\n# As Cataratas Místicas\nLocalizada no norte.",
            )
            # Arquivos ignorados pelo importador
            z.writestr(".obsidian/workspace.json", "{}")
            z.writestr("__MACOSX/._NotaPrincipal.md", "data")
            z.writestr("mapa.png", "fake_png_data")

        zip_bytes = zip_buffer.getvalue()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 3. Tentativa pelo Jogador -> Retorna 403 Forbidden
            res_jog = await ac.post(
                f"/api/v1/worlds/{world.id}/articles/import/obsidian",
                files={"file": ("cofre.zip", zip_bytes, "application/zip")},
                data={"use_folders_as_tags": "true"},
                headers=headers_jogador,
            )
            assert res_jog.status_code == 403, res_jog.text

            # 4. Importação pelo Mestre com pastas como tags -> Retorna 201 Created
            res_mestre = await ac.post(
                f"/api/v1/worlds/{world.id}/articles/import/obsidian",
                files={"file": ("cofre.zip", zip_bytes, "application/zip")},
                data={"use_folders_as_tags": "true"},
                headers=headers_mestre,
            )
            assert res_mestre.status_code == 201, res_mestre.text
            import_data = res_mestre.json()
            assert import_data["imported_count"] == 2
            assert import_data["skipped_count"] >= 3

            # 5. Verificar se os artigos foram gravados com os Defaults corretos no banco
            articles = await article_service.listar_artigos(db, world.id, UserRole.MESTRE)
            assert len(articles) == 2

            nota_main = next(a for a in articles if a.title == "NotaPrincipal")
            assert nota_main.visibility == VisibilityType.NULA  # Default Névoa Nula
            detail_main = await article_service.buscar_artigo(db, nota_main.id, world.id)
            assert "Visão Geral" in detail_main.content
            assert "História Secreta" in detail_main.content

            nota_cataratas = next(a for a in articles if a.title == "Cataratas")
            assert nota_cataratas.visibility == VisibilityType.NULA
            assert nota_cataratas.in_game_date == "1492-10-12"
            tag_names = {t.name for t in nota_cataratas.tags}
            assert ".natureza" in tag_names
            assert ".perigo" in tag_names
            assert ".Regiões" in tag_names  # Tag derivada da subpasta

            # Cleanup
            await db.delete(world)
            await db.delete(mestre)
            await db.delete(jogador)
            await db.commit()
