"""add_inventory_groups_and_items

Revision ID: a1b2c3d4e5f6
Revises: 8333d49194f3
Create Date: 2026-08-11 15:45:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '8333d49194f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tabela inventory_groups
    op.create_table(
        'inventory_groups',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('world_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('visibility', postgresql.ENUM('TOTAL', 'PARCIAL', 'NULA', name='visibility_type', create_type=False), nullable=False),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_inventory_groups_world_vis', 'inventory_groups', ['world_id', 'visibility'], unique=False)

    # 2. Tabela inventories
    op.create_table(
        'inventories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('world_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('owner_article_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('limit', sa.Integer(), nullable=True),
        sa.Column('visibility', postgresql.ENUM('TOTAL', 'PARCIAL', 'NULA', name='visibility_type', create_type=False), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['group_id'], ['inventory_groups.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['owner_article_id'], ['articles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_inventories_world_vis', 'inventories', ['world_id', 'visibility'], unique=False)
    op.create_index('idx_inventories_group', 'inventories', ['group_id'], unique=False)

    # 3. Tabela inventory_items
    op.create_table(
        'inventory_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('inventory_id', sa.UUID(), nullable=False),
        sa.Column('article_id', sa.UUID(), nullable=True),
        sa.Column('custom_name', sa.String(length=100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_inventory_items_inv', 'inventory_items', ['inventory_id'], unique=False)
    op.create_index('idx_inventory_items_art', 'inventory_items', ['article_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_inventory_items_art', table_name='inventory_items')
    op.drop_index('idx_inventory_items_inv', table_name='inventory_items')
    op.drop_table('inventory_items')
    op.drop_index('idx_inventories_group', table_name='inventories')
    op.drop_index('idx_inventories_world_vis', table_name='inventories')
    op.drop_table('inventories')
    op.drop_index('idx_inventory_groups_world_vis', table_name='inventory_groups')
    op.drop_table('inventory_groups')
