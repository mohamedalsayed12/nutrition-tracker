"""Barcode foods and personal API tokens

Revision ID: 7c1e2b9d4a10
Revises: 23a004073fe6
Create Date: 2026-10-22 23:05:00

"""
from alembic import op
import sqlalchemy as sa


revision = '7c1e2b9d4a10'
down_revision = '23a004073fe6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('food_logs') as batch:
        batch.alter_column('fdc_id', existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column('barcode', sa.String(length=14), nullable=True))
    op.create_table(
        'api_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('timezone', sa.String(length=64), nullable=False, server_default='UTC'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index('ix_api_tokens_user_id', 'api_tokens', ['user_id'])


def downgrade():
    op.drop_index('ix_api_tokens_user_id', table_name='api_tokens')
    op.drop_table('api_tokens')
    op.execute("DELETE FROM food_logs WHERE fdc_id IS NULL")
    with op.batch_alter_table('food_logs') as batch:
        batch.drop_column('barcode')
        batch.alter_column('fdc_id', existing_type=sa.Integer(), nullable=False)
