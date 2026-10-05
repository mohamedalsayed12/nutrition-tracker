from datetime import datetime, timezone

from flask_login import UserMixin
from extensions import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'<User: {self.username}>'

    def get_id(self):
        return str(self.uid)


##Save each user's daily calorie goal from the UserInfo calculator.
class CalorieTarget(db.Model):
    __tablename__ = "calorie_targets"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    calories = db.Column(db.Float, nullable=False)


##Keep the age and sex used for personal macro and micronutrient targets.
class NutritionTargets(db.Model):
    __tablename__ = "nutrition_targets"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    protein_min = db.Column(db.Float, nullable=False)
    protein_max = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    micronutrients = db.Column(db.JSON, nullable=False)


##Keep selected health conditions and optional care-plan targets per user.
class HealthPreferences(db.Model):
    __tablename__ = "health_preferences"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    conditions = db.Column(db.JSON, nullable=False, default=list)
    trimester = db.Column(db.Integer, nullable=True)
    custom_calories = db.Column(db.Float, nullable=True)
    custom_carbs = db.Column(db.Float, nullable=True)
    micronutrient_overrides = db.Column(db.JSON, nullable=False, default=dict)
    base_calories = db.Column(db.Float, nullable=True)
    base_carbs = db.Column(db.Float, nullable=True)
    base_protein_min = db.Column(db.Float, nullable=True)
    base_protein_max = db.Column(db.Float, nullable=True)


##Reject a repeated form submission so one click cannot save a meal twice.
class MealSubmission(db.Model):
    __tablename__ = "meal_submissions"

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), primary_key=True)
    token = db.Column(db.String(64), primary_key=True)


##Store a food's USDA ID, gram amount, and nutrient values for its meal entry.
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


##Store exercise entries separately so users can remove them individually.
class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"), nullable=False, index=True)
    activity = db.Column(db.String(200), nullable=False)
    logged_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
