"""Add order tables and fields

Revision ID: 4fd1021a820c
Revises: a2721c36789a
Create Date: 2025-06-23 14:32:44.162248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4fd1021a820c'
down_revision: Union[str, None] = 'a2721c36789a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('driver_locations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('driver_id', sa.UUID(), nullable=False),
    sa.Column('location', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_up', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('driver_id')
    )
    op.create_index(op.f('ix_driver_locations_id'), 'driver_locations', ['id'], unique=False)
    op.create_table('orders',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('customer_id', sa.UUID(), nullable=False),
    sa.Column('driver_id', sa.UUID(), nullable=False),
    sa.Column('pickup_location', sa.String(), nullable=False),
    sa.Column('recipient_details', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('goods_image_path', sa.String(), nullable=True),
    sa.Column('delivery_location', sa.String(), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('status', sa.Enum('CREATED', 'ASSIGNED', 'PICKED_UP', 'DELIVERED', 'CANCELLED', 'FAILED', name='orderstatus'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_up', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('order_status_history',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('order_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('CREATED', 'ASSIGNED', 'PICKED_UP', 'DELIVERED', 'CANCELLED', 'FAILED', name='orderstatus'), nullable=False),
    sa.Column('changed_by_id', sa.UUID(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_up', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_status_history_id'), 'order_status_history', ['id'], unique=False)
    op.create_table('proof_of_delivery',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('order_id', sa.UUID(), nullable=False),
    sa.Column('image_path', sa.String(), nullable=True),
    sa.Column('signature_path', sa.String(), nullable=True),
    sa.Column('uploaded_path', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_up', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('order_id')
    )
    op.create_index(op.f('ix_proof_of_delivery_id'), 'proof_of_delivery', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_proof_of_delivery_id'), table_name='proof_of_delivery')
    op.drop_table('proof_of_delivery')
    op.drop_index(op.f('ix_order_status_history_id'), table_name='order_status_history')
    op.drop_table('order_status_history')
    op.drop_table('orders')
    op.drop_index(op.f('ix_driver_locations_id'), table_name='driver_locations')
    op.drop_table('driver_locations')
    # ### end Alembic commands ###
