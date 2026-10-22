from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from database import db
from models import CalorieTarget, NutritionTargets, UserActivityBaseline, UserMeasurements
from oauth2 import current_user_id
from schemas import CalorieGoal, NutritionSetup, validate_body
from services.goals import set_nutrition_goals
from services.nutrient_targets import UNTRACKED
from services.settings import set_calories


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
    return jsonify(configured=True, age=target.age, sex=target.sex, protein_min=target.protein_min,
                   protein_max=target.protein_max, carbs=target.carbs,
                   micronutrients=[row for row in target.micronutrients or [] if row.get("name") not in UNTRACKED],
                   height_cm=measurements.height_cm if measurements else None,
                   weight_kg=measurements.weight_kg if measurements else None,
                   activity_level=baseline.activity_level if baseline else None)


@router.put("/nutrition")
@jwt_required()
@validate_body(NutritionSetup)
def update_nutrition(data):
    return jsonify(set_nutrition_goals(current_user_id(), data))
