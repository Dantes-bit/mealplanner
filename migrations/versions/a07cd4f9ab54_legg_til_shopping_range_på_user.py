"""legg til shopping_range på User

Revision ID: a07cd4f9ab54
Revises: 65b0458b4547
Create Date: 2026-08-27 13:52:51.358530

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a07cd4f9ab54'
down_revision = '65b0458b4547'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('shopping_range_start', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('shopping_range_end', sa.Integer(), nullable=False, server_default='6'))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('shopping_range_end')
        batch_op.drop_column('shopping_range_start')
