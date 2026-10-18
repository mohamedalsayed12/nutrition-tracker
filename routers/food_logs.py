from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from database import db
from models import FoodLog
from oauth2 import current_user_id
from routers.common import owned_record, paginated
from schemas import FoodLogCreate, validate_body
from services.logs import create_food, food_values, invalidate_day, serialize_food


router = Blueprint("food_logs", __name__)


@router.get("")
@jwt_required()
def list_food_logs():
    return paginated(FoodLog, serialize_food)


@router.post("")
@jwt_required()
@validate_body(FoodLogCreate)
def create_food_log(data):
    return jsonify(serialize_food(create_food(current_user_id(), data))), 201


@router.get("/<int:log_id>")
@jwt_required()
def get_food_log(log_id):
    return jsonify(serialize_food(owned_record(FoodLog, log_id)))


@router.put("/<int:log_id>")
@jwt_required()
@validate_body(FoodLogCreate)
def update_food_log(log_id, data):
    log = owned_record(FoodLog, log_id)
    for key, value in food_values(data).items():
        setattr(log, key, value)
    invalidate_day(log)
    db.session.commit()
    return jsonify(serialize_food(log))


@router.delete("/<int:log_id>")
@jwt_required()
def delete_food_log(log_id):
    log = owned_record(FoodLog, log_id)
    invalidate_day(log)
    db.session.delete(log)
    db.session.commit()
    return "", 204
