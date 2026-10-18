"""Add onboarding profiles for registration body metrics

Revision ID: c8d9e0f1a2b3
Revises: a1b2c3d4e5f6
Create Date: 2026-10-18 20:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c8d9e0f1a2b3"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if "onboarding_profiles" not in existing:
        op.create_table(
            "onboarding_profiles",
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("age", sa.Integer(), nullable=False),
            sa.Column("sex", sa.String(length=10), nullable=False),
            sa.Column("height_cm", sa.Float(), nullable=False),
            sa.Column("weight_kg", sa.Float(), nullable=False),
            sa.Column("activity_level", sa.String(length=30), nullable=False),
            sa.Column("goal", sa.String(length=20), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.uid"]),
            sa.PrimaryKeyConstraint("user_id"),
        )


def downgrade():
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if "onboarding_profiles" in existing:
        op.drop_table("onboarding_profiles")
