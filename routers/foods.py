from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_login import current_user

from services.barcode import fetch_open_food_facts, find_usda_barcode, normalise_barcode
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


@router.get("/foods/barcode/<code>")
def barcode(code):
    """The food for a scanned barcode, with its serving sizes, ready to log.

    USDA Branded Foods first; Open Food Facts when USDA has no match.
    """
    code = normalise_barcode(code)
    if code is None:
        abort(400, description="A barcode has 8 to 14 digits.")
    try:
        client = get_food_client()
    except ValueError as error:
        abort(503, description=str(error))
    usda = find_usda_barcode(client, code)
    if usda is not None:
        try:
            food = client.get_food(usda.fdc_id)
        except Exception:
            abort(502, description="Food details are temporarily unavailable.")
        summary = dict(fdc_id=food.fdc_id, barcode=None, source="USDA")
    else:
        try:
            food = fetch_open_food_facts(code)
        except LookupError as error:
            abort(502, description=str(error))
        if food is None:
            abort(404, description="This barcode isn't in USDA or Open Food Facts yet. Try searching by name.")
        summary = dict(fdc_id=None, barcode=code, source="Open Food Facts")
    kcal = next((n.amount for n in food.nutrients if n.name == "Energy" and n.unit_name.lower() == "kcal"), None)
    return jsonify(food=dict(summary, description=food.description, brand_name=getattr(food, "brand_name", None),
                             data_type=food.data_type, gtin_upc=code, kcal_per_100g=kcal),
                   measures=food_measures(food))


@router.get("/exercises")
def exercises():
    return jsonify(exercises=search_exercises(request.args.get("q", "").strip()))
