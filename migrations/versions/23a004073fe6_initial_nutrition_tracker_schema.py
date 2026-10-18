"""Initial nutrition tracker schema

Revision ID: 23a004073fe6
Revises:
Create Date: 2026-10-18 16:10:28.816960

"""
from alembic import op
import sqlalchemy as sa


revision = '23a004073fe6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if 'users' not in existing:
        op.create_table('users',
        sa.Column('uid', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('uid'),
        sa.UniqueConstraint('email')
        )
    if 'activity_logs' not in existing:
        op.create_table('activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('activity', sa.String(length=200), nullable=False),
        sa.Column('logged_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('id')
        )
    if 'calorie_targets' not in existing:
        op.create_table('calorie_targets',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('calories', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('user_id')
        )
    if 'food_logs' not in existing:
        op.create_table('food_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('meal', sa.String(length=20), nullable=False),
        sa.Column('fdc_id', sa.Integer(), nullable=False),
        sa.Column('food_name', sa.String(length=300), nullable=False),
        sa.Column('grams', sa.Float(), nullable=False),
        sa.Column('nutrients', sa.JSON(), nullable=False),
        sa.Column('logged_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('id')
        )
    if 'health_preferences' not in existing:
        op.create_table('health_preferences',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=False),
        sa.Column('trimester', sa.Integer(), nullable=True),
        sa.Column('custom_calories', sa.Float(), nullable=True),
        sa.Column('custom_carbs', sa.Float(), nullable=True),
        sa.Column('custom_protein', sa.Float(), nullable=True),
        sa.Column('custom_fat', sa.Float(), nullable=True),
        sa.Column('micronutrient_overrides', sa.JSON(), nullable=False),
        sa.Column('base_calories', sa.Float(), nullable=True),
        sa.Column('base_carbs', sa.Float(), nullable=True),
        sa.Column('base_protein_min', sa.Float(), nullable=True),
        sa.Column('base_protein_max', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('user_id')
        )
    if 'macro_splits' not in existing:
        op.create_table('macro_splits',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('carbs_percent', sa.Float(), nullable=False),
        sa.Column('protein_percent', sa.Float(), nullable=False),
        sa.Column('fat_percent', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('user_id')
        )
    if 'meal_submissions' not in existing:
        op.create_table('meal_submissions',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('user_id', 'token')
        )
    if 'nutrition_targets' not in existing:
        op.create_table('nutrition_targets',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('sex', sa.String(length=10), nullable=False),
        sa.Column('protein_min', sa.Float(), nullable=False),
        sa.Column('protein_max', sa.Float(), nullable=False),
        sa.Column('carbs', sa.Float(), nullable=False),
        sa.Column('micronutrients', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('user_id')
        )
    if 'saved_eating_days' not in existing:
        op.create_table('saved_eating_days',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('saved_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('user_id', 'day')
        )
    if 'user_activity_baselines' not in existing:
        op.create_table('user_activity_baselines',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('activity_level', sa.String(length=30), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('user_id')
        )
    if 'user_measurements' not in existing:
        op.create_table('user_measurements',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('height_cm', sa.Float(), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('user_id')
        )
    if 'exercise_details' not in existing:
        op.create_table('exercise_details',
        sa.Column('activity_log_id', sa.Integer(), nullable=False),
        sa.Column('duration_minutes', sa.Float(), nullable=False),
        sa.Column('calories_burned', sa.Float(), nullable=False),
        sa.Column('activity_type', sa.String(length=30), nullable=False),
        sa.Column('met', sa.Float(), nullable=False),
        sa.Column('height_cm', sa.Float(), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['activity_log_id'], ['activity_logs.id'], ),
        sa.PrimaryKeyConstraint('activity_log_id')
        )
    if 'exercise_target_credits' not in existing:
        op.create_table('exercise_target_credits',
        sa.Column('activity_log_id', sa.Integer(), nullable=False),
        sa.Column('extra', sa.Boolean(), nullable=False),
        sa.Column('active_calories', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['activity_log_id'], ['activity_logs.id'], ),
        sa.PrimaryKeyConstraint('activity_log_id')
        )
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("health_preferences")}
    for name in ("custom_protein", "custom_fat"):
        if name not in columns:
            op.add_column("health_preferences", sa.Column(name, sa.Float(), nullable=True))
    for table in ("food_logs", "activity_logs"):
        name = f"ix_{table}_user_id"
        indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table)}
        if name not in indexes:
            op.create_index(name, table, ["user_id"])


def downgrade():
    op.drop_table('exercise_target_credits')
    op.drop_table('exercise_details')
    op.drop_table('user_measurements')
    op.drop_table('user_activity_baselines')
    op.drop_table('saved_eating_days')
    op.drop_table('nutrition_targets')
    op.drop_table('meal_submissions')
    op.drop_table('macro_splits')
    op.drop_table('health_preferences')
    with op.batch_alter_table('food_logs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_food_logs_user_id'))

    op.drop_table('food_logs')
    op.drop_table('calorie_targets')
    with op.batch_alter_table('activity_logs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_activity_logs_user_id'))

    op.drop_table('activity_logs')
    op.drop_table('users')
