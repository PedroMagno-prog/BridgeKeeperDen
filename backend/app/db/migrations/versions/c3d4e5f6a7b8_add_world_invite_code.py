"""add_world_invite_code

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-12 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Adicionar coluna invite_code como nullable
    op.add_column('worlds', sa.Column('invite_code', sa.String(length=20), nullable=True))

    # 2. Preencher valores únicos para linhas pré-existentes
    op.execute("""
        UPDATE worlds
        SET invite_code = substring(md5(random()::text || id::text) from 1 for 10)
        WHERE invite_code IS NULL;
    """)

    # 3. Alterar coluna para NOT NULL e criar index e unique constraint
    op.alter_column('worlds', 'invite_code', nullable=False)
    op.create_index(op.f('ix_worlds_invite_code'), 'worlds', ['invite_code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_worlds_invite_code'), table_name='worlds')
    op.drop_column('worlds', 'invite_code')
