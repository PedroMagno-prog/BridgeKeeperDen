"""etapa7_folders_and_article_content

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-13 12:46:00.000000

"""
from collections import defaultdict
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Criar a tabela article_folders (se não existir)
    has_article_folders = bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'article_folders')"
    )).scalar()

    if not has_article_folders:
        op.create_table(
            'article_folders',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('world_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('parent_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['parent_id'], ['article_folders.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_article_folders_world_id', 'article_folders', ['world_id'])
        op.create_index('ix_article_folders_parent_id', 'article_folders', ['parent_id'])

    # 2. Adicionar colunas folder_id e content na tabela articles (se não existirem)
    has_folder_id = bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'articles' AND column_name = 'folder_id')"
    )).scalar()

    if not has_folder_id:
        op.add_column('articles', sa.Column('folder_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_articles_folder_id', 'articles', 'article_folders', ['folder_id'], ['id'], ondelete='SET NULL')
        op.create_index('ix_articles_folder_id', 'articles', ['folder_id'])

    has_content = bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'articles' AND column_name = 'content')"
    )).scalar()

    if not has_content:
        op.add_column('articles', sa.Column('content', sa.Text(), nullable=False, server_default=''))

    # 3. Migração de Dados: Concatenar seções existentes em formato Markdown
    has_sections = bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'article_sections')"
    )).scalar()

    if has_sections:
        res = bind.execute(sa.text("""
            SELECT article_id, title, content, order_index
            FROM article_sections
            ORDER BY article_id, order_index ASC
        """))
        rows = res.fetchall()

        articles_sections = defaultdict(list)
        for article_id, title, content, order_index in rows:
            articles_sections[article_id].append((title, content or ""))

        for article_id, sections in articles_sections.items():
            blocks = []
            for title, content in sections:
                t_clean = (title or "").strip()
                c_clean = (content or "").strip()
                if t_clean:
                    blocks.append(f"# {t_clean}\n\n{c_clean}".strip())
                elif c_clean:
                    blocks.append(c_clean)
            concatenated = "\n\n".join(b for b in blocks if b)
            bind.execute(
                sa.text("UPDATE articles SET content = :content WHERE id = :article_id"),
                {"content": concatenated, "article_id": article_id}
            )

        # Remover tabela article_sections
        op.drop_table('article_sections')


def downgrade() -> None:
    bind = op.get_bind()

    # 1. Recriar a tabela article_sections (se não existir)
    has_sections = bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'article_sections')"
    )).scalar()

    if not has_sections:
        op.create_table(
            'article_sections',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('article_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('title', sa.String(length=150), nullable=False),
            sa.Column('content', sa.Text(), nullable=False, server_default=''),
            sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('image_url', sa.String(length=500), nullable=True),
            sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # 2. Remover colunas folder_id e content da tabela articles
    has_folder_id = bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'articles' AND column_name = 'folder_id')"
    )).scalar()
    if has_folder_id:
        op.drop_constraint('fk_articles_folder_id', 'articles', type_='foreignkey')
        op.drop_index('ix_articles_folder_id', table_name='articles')
        op.drop_column('articles', 'folder_id')

    has_content = bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'articles' AND column_name = 'content')"
    )).scalar()
    if has_content:
        op.drop_column('articles', 'content')

    # 3. Remover a tabela article_folders
    has_folders = bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'article_folders')"
    )).scalar()
    if has_folders:
        op.drop_index('ix_article_folders_parent_id', table_name='article_folders')
        op.drop_index('ix_article_folders_world_id', table_name='article_folders')
        op.drop_table('article_folders')
