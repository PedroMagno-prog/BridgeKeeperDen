"""add_quests_and_objectives

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-12 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Definir os Enums
    quest_status_enum = postgresql.ENUM(
        'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'ON_HOLD',
        name='quest_status',
        create_type=False
    )

    quest_category_enum = postgresql.ENUM(
        'MAIN_QUEST', 'SIDE_QUEST', 'MONSTER_HUNT', 'ARTIFACT_SEARCH', 'OUTPOST', 'FACTION',
        name='quest_category',
        create_type=False
    )

    visibility_type_enum = postgresql.ENUM(
        'TOTAL', 'PARCIAL', 'NULA',
        name='visibility_type',
        create_type=False
    )

    # Garantir que os tipos enum existam no banco Postgres
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE quest_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'ON_HOLD');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE quest_category AS ENUM ('MAIN_QUEST', 'SIDE_QUEST', 'MONSTER_HUNT', 'ARTIFACT_SEARCH', 'OUTPOST', 'FACTION');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 2. Criar tabela quests
    op.create_table(
        'quests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('world_id', sa.UUID(), nullable=False),
        sa.Column('article_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('category', quest_category_enum, nullable=False),
        sa.Column('status', quest_status_enum, nullable=False),
        sa.Column('visibility', visibility_type_enum, nullable=False),
        sa.Column('rewards', sa.Text(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Criar tabela quest_objectives
    op.create_table(
        'quest_objectives',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('quest_id', sa.UUID(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['quest_id'], ['quests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('quest_objectives')
    op.drop_table('quests')
    op.execute("DROP TYPE IF EXISTS quest_category")
    op.execute("DROP TYPE IF EXISTS quest_status")
