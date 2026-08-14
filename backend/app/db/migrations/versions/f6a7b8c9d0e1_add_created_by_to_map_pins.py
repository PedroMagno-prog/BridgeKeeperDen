"""add_created_by_to_map_pins

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-14 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Adiciona a coluna created_by na tabela map_pins (se não existir)
    has_created_by = bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'map_pins' AND column_name = 'created_by')"
    )).scalar()

    if not has_created_by:
        op.add_column(
            'map_pins',
            sa.Column(
                'created_by',
                postgresql.UUID(as_uuid=True),
                nullable=True,
                comment='ID do usuario criador do marcador'
            )
        )
        op.create_foreign_key(
            'fk_map_pins_created_by',
            'map_pins',
            'users',
            ['created_by'],
            ['id'],
            ondelete='SET NULL'
        )
        op.create_index('ix_map_pins_created_by', 'map_pins', ['created_by'])


def downgrade() -> None:
    op.drop_index('ix_map_pins_created_by', table_name='map_pins')
    op.drop_constraint('fk_map_pins_created_by', 'map_pins', type_='foreignkey')
    op.drop_column('map_pins', 'created_by')
