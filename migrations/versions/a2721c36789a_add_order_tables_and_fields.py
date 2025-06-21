"""Add order tables and fields

Revision ID: a2721c36789a
Revises: 74ca22914438
Create Date: 2025-06-21 14:25:33.199784
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a2721c36789a'
down_revision: Union[str, None] = '74ca22914438'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    user_role_enum = postgresql.ENUM('CUSTOMER', 'ADMIN', 'DISPATCHER', name='userrole')
    user_role_enum.create(op.get_bind())

    op.create_table(
        'token_blacklist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('blacklisted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_up', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_token_blacklist_id'), 'token_blacklist', ['id'], unique=False)
    op.create_index(op.f('ix_token_blacklist_token'), 'token_blacklist', ['token'], unique=True)

    op.add_column('users', sa.Column('role', user_role_enum, nullable=False))
    op.add_column('users', sa.Column('staff_id', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'users', ['staff_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'users', type_='unique')
    op.drop_column('users', 'staff_id')
    op.drop_column('users', 'role')

    op.drop_index(op.f('ix_token_blacklist_token'), table_name='token_blacklist')
    op.drop_index(op.f('ix_token_blacklist_id'), table_name='token_blacklist')
    op.drop_table('token_blacklist')

    user_role_enum = postgresql.ENUM('CUSTOMER', 'ADMIN', 'DISPATCHER', name='userrole')
    user_role_enum.drop(op.get_bind())
