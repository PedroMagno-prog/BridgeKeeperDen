"""
Teste isolado: simula exatamente o UPDATE route para diagnosticar o bug de tags.
"""
import asyncio
import sys
sys.path.insert(0, ".")

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from app.db.models.article import Article
from app.db.models.article_tag import ArticleTag

DATABASE_URL = "postgresql+asyncpg://postgres:coti@localhost:5433/bridgekeeper"

async def test():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Buscar artigo com 2 tags (.Local, .Ruinas)
        result = await db.execute(
            select(Article)
            .options(
                selectinload(Article.tags),
                selectinload(Article.sections),
                selectinload(Article.inventory_items),
            )
            .limit(1)
        )
        article = result.scalar_one_or_none()
        if not article:
            print("ERRO: Nenhum artigo!")
            return

        print(f"ANTES: artigo='{article.title}', tags={[t.name for t in article.tags]}")

        # Simular atualizar_artigo: delete ORM + insert novos
        new_tags = [".Local", ".Ruinas", ".Nova"]

        for tag in list(article.tags):
            await db.delete(tag)
        await db.flush()

        for tag_name in new_tags:
            db.add(ArticleTag(article_id=article.id, name=tag_name))
        await db.flush()

        await db.commit()

        # Verificar no banco via SQL raw
        count = await db.scalar(
            text("SELECT COUNT(*) FROM article_tags WHERE article_id = :id"),
            {"id": str(article.id)}
        )
        print(f"APOS COMMIT - SQL raw: {count} tags")

        # Simular expunge_all + reload
        db.expunge_all()

        result2 = await db.execute(
            select(Article)
            .options(
                selectinload(Article.tags),
                selectinload(Article.sections),
                selectinload(Article.inventory_items),
            )
            .where(Article.id == article.id)
        )
        loaded = result2.scalar_one()
        print(f"APOS RELOAD - ORM: {len(loaded.tags)} tags -> {[t.name for t in loaded.tags]}")

        # Restaurar 2 tags originais
        for tag in list(loaded.tags):
            await db.delete(tag)
        await db.flush()
        for name in [".Local", ".Ruinas"]:
            db.add(ArticleTag(article_id=article.id, name=name))
        await db.commit()
        print("Restaurado ao estado original.")

    await engine.dispose()

asyncio.run(test())
