"""add delete cascade to payment

Revision ID: e749695b574e
Revises: 60117284068b
Create Date: 2025-06-26 20:34:19.746547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e749695b574e'
down_revision: Union[str, None] = '60117284068b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('payments_order_id_fkey'), 'payments', type_='foreignkey')
    op.create_foreign_key(None, 'payments', 'orders', ['order_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'payments', type_='foreignkey')
    op.create_foreign_key(op.f('payments_order_id_fkey'), 'payments', 'orders', ['order_id'], ['id'])
    op.create_table('spatial_ref_sys',
    sa.Column('srid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('auth_name', sa.VARCHAR(length=256), autoincrement=False, nullable=True),
    sa.Column('auth_srid', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('srtext', sa.VARCHAR(length=2048), autoincrement=False, nullable=True),
    sa.Column('proj4text', sa.VARCHAR(length=2048), autoincrement=False, nullable=True),
    sa.CheckConstraint('srid > 0 AND srid <= 998999', name=op.f('spatial_ref_sys_srid_check')),
    sa.PrimaryKeyConstraint('srid', name=op.f('spatial_ref_sys_pkey'))
    )
    # ### end Alembic commands ###

