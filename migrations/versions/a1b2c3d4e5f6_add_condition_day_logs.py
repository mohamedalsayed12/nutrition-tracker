"""Add condition_day_logs for day-scoped medical conditions

Revision ID: a1b2c3d4e5f6
Revises: 23a004073fe6
Create Date: 2026-10-18 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '23a004073fe6'
branch_labels = None
depends_on = None


def upgrade():
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if 'condition_day_logs' not in existing:
        op.create_table(
            'condition_day_logs',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('day', sa.Date(), nullable=False),
            sa.Column('conditions', sa.JSON(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.uid']),
            sa.PrimaryKeyConstraint('user_id', 'day'),
        )


def downgrade():
    op.drop_table('condition_day_logs')
