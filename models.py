from datetime import datetime, timezone
from database import db

class User(db.Model):
    __tablename__ = 'users'

    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'<User: {self.username}>'


class OnboardingProfile(db.Model):
    """Body metrics collected at registration before a calorie goal is chosen."""

    __tablename__ = "onboarding_profiles"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    activity_level = db.Column(db.String(30), nullable=False)
    goal = db.Column(db.String(20), nullable=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

class CalorieTarget(db.Model):
    __tablename__ = "calorie_targets"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    calories = db.Column(db.Float, nullable=False)


class NutritionTargets(db.Model):
    __tablename__ = "nutrition_targets"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    protein_min = db.Column(db.Float, nullable=False)
    protein_max = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    micronutrients = db.Column(db.JSON, nullable=False)


class UserMeasurements(db.Model):
    __tablename__ = "user_measurements"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    height_cm = db.Column(db.Float, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)


class UserActivityBaseline(db.Model):
    __tablename__ = "user_activity_baselines"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    activity_level = db.Column(db.String(30), nullable=False)
    changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class MacroSplit(db.Model):
    __tablename__ = "macro_splits"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    carbs_percent = db.Column(db.Float, nullable=False)
    protein_percent = db.Column(db.Float, nullable=False)
    fat_percent = db.Column(db.Float, nullable=False)


class HealthPreferences(db.Model):
    __tablename__ = "health_preferences"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    conditions = db.Column(db.JSON, nullable=False, default=list)
    trimester = db.Column(db.Integer, nullable=True)
    custom_calories = db.Column(db.Float, nullable=True)
    custom_carbs = db.Column(db.Float, nullable=True)
    custom_protein = db.Column(db.Float, nullable=True)
    custom_fat = db.Column(db.Float, nullable=True)
    micronutrient_overrides = db.Column(db.JSON, nullable=False, default=dict)
    base_calories = db.Column(db.Float, nullable=True)
    base_carbs = db.Column(db.Float, nullable=True)
    base_protein_min = db.Column(db.Float, nullable=True)
    base_protein_max = db.Column(db.Float, nullable=True)


class MealSubmission(db.Model):
    __tablename__ = "meal_submissions"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    token = db.Column(db.String(64), primary_key=True)


class FoodLog(db.Model):
    __tablename__ = "food_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), nullable=False, index=True)
    meal = db.Column(db.String(20), nullable=False)
    fdc_id = db.Column(db.Integer, nullable=False)
    food_name = db.Column(db.String(300), nullable=False)
    grams = db.Column(db.Float, nullable=False)
    nutrients = db.Column(db.JSON, nullable=False)
    logged_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SavedEatingDay(db.Model):
    __tablename__ = "saved_eating_days"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    day = db.Column(db.Date, primary_key=True)
    saved_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class ConditionDayLog(db.Model):
    """Day-scoped medical conditions that adjust nutrient targets for that day.

    Chronic conditions stay in HealthPreferences. Logging menstruation here
    raises iron and vitamin C targets for the selected UTC day.
    """

    __tablename__ = "condition_day_logs"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    day = db.Column(db.Date, primary_key=True)
    conditions = db.Column(db.JSON, nullable=False, default=list)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), nullable=False, index=True)
    activity = db.Column(db.String(200), nullable=False)
    details = db.relationship("ExerciseDetails", uselist=False, cascade="all, delete-orphan")
    target_credit = db.relationship("ExerciseTargetCredit", uselist=False, cascade="all, delete-orphan")
    logged_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ExerciseDetails(db.Model):
    __tablename__ = "exercise_details"

    activity_log_id = db.Column(db.Integer, db.ForeignKey("activity_logs.id"), primary_key=True)
    duration_minutes = db.Column(db.Float, nullable=False)
    calories_burned = db.Column(db.Float, nullable=False)
    activity_type = db.Column(db.String(30), nullable=False)
    met = db.Column(db.Float, nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)


class ExerciseTargetCredit(db.Model):
    __tablename__ = "exercise_target_credits"

    activity_log_id = db.Column(db.Integer, db.ForeignKey("activity_logs.id"), primary_key=True)
    extra = db.Column(db.Boolean, nullable=False)
    active_calories = db.Column(db.Float, nullable=False)
