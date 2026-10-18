from datetime import datetime, timezone
from decimal import Decimal
import os

from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import db
from models import CalorieTarget, HealthPreferences, NutritionTargets
from schemas import VoiceParseInput, validate_body
from services.barcode_lookup import lookup_barcode
from services.calc import configured_micronutrients, food_measures, scaled_food_nutrients
from services.condition_days import day_condition_list
from services.food_search import get_food_client, search_exercises, search_foods
from services.nutrient_scoring import food_nutrient_density
from services.voice_parse import parse_voice_log


router = Blueprint("foods", __name__)


@router.get("/foods")
@jwt_required(optional=True)
def foods():
    identity = get_jwt_identity()
    return jsonify(foods=search_foods(request.args.get("q", "").strip().lower(),
                                     int(identity) if identity else None))


@router.get("/foods/barcode/<code>")
@jwt_required(optional=True)
def food_barcode(code):
    if not os.getenv("FDC_API_KEY"):
        abort(503, description="Food search is not configured.")
    try:
        return jsonify(lookup_barcode(code))
    except ValueError as error:
        abort(404 if "No matching" in str(error) else 400, description=str(error))
    except Exception:
        abort(502, description="Barcode lookup is temporarily unavailable.")


@router.post("/foods/voice-parse")
@jwt_required()
@validate_body(VoiceParseInput)
def food_voice_parse(data):
    parsed = parse_voice_log(data.transcript, default_meal=data.default_meal)
    foods = []
    if os.getenv("FDC_API_KEY"):
        try:
            foods = search_foods(parsed["food_query"])
        except Exception:
            foods = []
    return jsonify(**parsed, foods=foods)


def _density_for_user(user_id, nutrients):
    nutrition = db.session.get(NutritionTargets, user_id) if user_id else None
    if nutrition is None:
        return food_nutrient_density(nutrients)
    preferences = db.session.get(HealthPreferences, user_id)
    day = datetime.now(timezone.utc).date()
    targets = configured_micronutrients(
        nutrition.age, nutrition.sex, preferences,
        extra_conditions=day_condition_list(user_id, day),
    )
    calorie_target = db.session.get(CalorieTarget, user_id)
    daily_calories = calorie_target.calories if calorie_target else None
    if daily_calories is None and preferences is not None:
        daily_calories = preferences.custom_calories or preferences.base_calories
    return food_nutrient_density(nutrients, targets=targets, daily_calories=daily_calories)


@router.get("/foods/<int:fdc_id>")
@jwt_required(optional=True)
def food_detail(fdc_id):
    try:
        client = get_food_client()
    except ValueError as error:
        abort(503, description=str(error))
    try:
        food = client.get_food(fdc_id)
    except Exception:
        abort(502, description="Food details are temporarily unavailable.")
    nutrients = scaled_food_nutrients(food, Decimal("100"))
    identity = get_jwt_identity()
    user_id = int(identity) if identity else None
    return jsonify(
        fdc_id=fdc_id,
        description=food.description,
        nutrients=nutrients,
        measures=food_measures(food),
        density=_density_for_user(user_id, nutrients),
    )


@router.get("/foods/<int:fdc_id>/measures")
def measures(fdc_id):
    try:
        client = get_food_client()
    except ValueError as error:
        abort(503, description=str(error))
    try:
        food = client.get_food(fdc_id)
    except Exception:
        abort(502, description="Serving sizes are temporarily unavailable.")
    return jsonify(measures=food_measures(food))


@router.get("/exercises")
def exercises():
    return jsonify(exercises=search_exercises(request.args.get("q", "").strip()))
