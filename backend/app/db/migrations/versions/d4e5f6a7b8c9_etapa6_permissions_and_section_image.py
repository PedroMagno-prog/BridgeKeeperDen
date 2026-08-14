"""etapa6_permissions_and_section_image

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-12 14:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Adicionar valor 'CONTROLADO' ao enum visibility_type (se não existir)
    bind = op.get_bind()
    has_controlado = bind.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid 
            WHERE t.typname = 'visibility_type' AND e.enumlabel = 'CONTROLADO'
        )
    """)).scalar()

    if not has_controlado:
        op.execute(sa.text("ALTER TYPE visibility_type ADD VALUE 'CONTROLADO'"))

    # 2. Adicionar coluna image_url em article_sections
    op.add_column('article_sections', sa.Column('image_url', sa.String(length=500), nullable=True))

    # 3. Criar tabela article_user_permissions
    op.create_table(
        'article_user_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('visibility', postgresql.ENUM('TOTAL', 'PARCIAL', 'CONTROLADO', 'NULA', name='visibility_type', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_id', 'user_id', name='uq_article_user_perm')
    )

    # 4. Criar tabela inventory_user_permissions
    op.create_table(
        'inventory_user_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inventory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('visibility', postgresql.ENUM('TOTAL', 'PARCIAL', 'CONTROLADO', 'NULA', name='visibility_type', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('inventory_id', 'user_id', name='uq_inventory_user_perm')
    )

    # 5. Criar tabela inventory_group_user_permissions
    op.create_table(
        'inventory_group_user_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('visibility', postgresql.ENUM('TOTAL', 'PARCIAL', 'CONTROLADO', 'NULA', name='visibility_type', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['inventory_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'user_id', name='uq_group_user_perm')
    )


def downgrade() -> None:
    op.drop_table('inventory_group_user_permissions')
    op.drop_table('inventory_user_permissions')
    op.drop_table('article_user_permissions')
    op.drop_column('article_sections', 'image_url')
