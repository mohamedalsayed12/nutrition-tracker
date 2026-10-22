from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_login import current_user

from services.calc import food_measures
from services.food_search import get_food_client, search_exercises, search_foods


router = Blueprint("foods", __name__)


@router.get("/foods")
@jwt_required(optional=True)
def foods():
    # API clients sign in with a token; the web pages sign in with a session.
    identity = get_jwt_identity()
    if identity:
        user_id = int(identity)
    elif current_user.is_authenticated:
        user_id = current_user.uid
    else:
        user_id = None
    return jsonify(foods=search_foods(request.args.get("q", "").strip().lower(), user_id))


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
