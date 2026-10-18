from decimal import Decimal

from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.calc import food_measures, scaled_food_nutrients
from services.food_search import get_food_client, search_exercises, search_foods


router = Blueprint("foods", __name__)


@router.get("/foods")
@jwt_required(optional=True)
def foods():
    identity = get_jwt_identity()
    return jsonify(foods=search_foods(request.args.get("q", "").strip().lower(),
                                     int(identity) if identity else None))


@router.get("/foods/<int:fdc_id>")
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
    return jsonify(
        fdc_id=fdc_id,
        description=food.description,
        nutrients=nutrients,
        measures=food_measures(food),
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
