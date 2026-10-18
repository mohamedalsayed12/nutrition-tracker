from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from database import db
from models import CalorieTarget, NutritionTargets, OnboardingProfile, UserActivityBaseline, UserMeasurements
from oauth2 import current_user_id
from schemas import CalorieGoal, GoalChoice, NutritionSetup, validate_body
from services.goals import set_nutrition_goals
from services.settings import set_calories
from services.users import set_goal_from_profile


router = Blueprint("goals", __name__)


@router.get("/calories")
@jwt_required()
def get_calories():
    target = db.session.get(CalorieTarget, current_user_id())
    return jsonify(calories=target.calories if target else None)


@router.put("/calories")
@jwt_required()
@validate_body(CalorieGoal)
def update_calories(data):
    return jsonify(set_calories(current_user_id(), data.calories))


@router.get("/nutrition")
@jwt_required()
def nutrition():
    user_id = current_user_id()
    target = db.session.get(NutritionTargets, user_id)
    if target is None:
        return jsonify(configured=False)
    measurements = db.session.get(UserMeasurements, user_id)
    baseline = db.session.get(UserActivityBaseline, user_id)
    profile = db.session.get(OnboardingProfile, user_id)
    return jsonify(configured=True, age=target.age, sex=target.sex, protein_min=target.protein_min,
                   protein_max=target.protein_max, carbs=target.carbs, micronutrients=target.micronutrients,
                   height_cm=measurements.height_cm if measurements else None,
                   weight_kg=measurements.weight_kg if measurements else None,
                   activity_level=baseline.activity_level if baseline else None,
                   goal=profile.goal if profile else None)


@router.put("/nutrition")
@jwt_required()
@validate_body(NutritionSetup)
def update_nutrition(data):
    return jsonify(set_nutrition_goals(current_user_id(), data))


@router.put("/goal")
@jwt_required()
@validate_body(GoalChoice)
def choose_goal(data):
    """Apply calorie and macro targets from the registration profile + chosen goal."""
    return jsonify(set_goal_from_profile(current_user_id(), data.goal))
