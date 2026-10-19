"""Store timestamps with a timezone, record the timezone of saved days,
and drop the unused meal_submissions table.

Existing timestamps were written as UTC, so they are converted with
AT TIME ZONE 'UTC' to keep the same instant.

Revision ID: 7e1c5b9a2d40
Revises: 23a004073fe6
Create Date: 2026-10-19 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "7e1c5b9a2d40"
down_revision = "23a004073fe6"
branch_labels = None
depends_on = None


TIMESTAMP_COLUMNS = (
    ("food_logs", "logged_at"),
    ("activity_logs", "logged_at"),
    ("saved_eating_days", "saved_at"),
    ("user_activity_baselines", "changed_at"),
)


def upgrade():
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table, column,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=False,
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
    op.add_column(
        "saved_eating_days",
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
    )
    op.drop_table("meal_submissions")


def downgrade():
    op.create_table(
        "meal_submissions",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.uid"]),
        sa.PrimaryKeyConstraint("user_id", "token"),
    )
    op.drop_column("saved_eating_days", "timezone")
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table, column,
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
