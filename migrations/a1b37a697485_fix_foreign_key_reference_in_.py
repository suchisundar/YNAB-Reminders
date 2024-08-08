"""Fix foreign key reference in Transaction model

Revision ID: a1b37a697485
Revises: 
Create Date: 2024-08-07 13:30:24.984165

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid


# revision identifiers, used by Alembic.
revision = 'a1b37a697485'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add a column to the 'transaction' table in the 'ynab' bind
    with op.batch_alter_table('transaction', schema='ynab') as batch_op:
        batch_op.add_column(sa.Column('transaction_id', sa.String(), nullable=False, default=lambda: str(uuid.uuid4())))
        batch_op.create_unique_constraint(None, 'transaction', ['transaction_id'])

def downgrade():
    # Drop the column from the 'transaction' table in the 'ynab' bind
    with op.batch_alter_table('transaction', schema='ynab') as batch_op:
        batch_op.drop_column('transaction_id')