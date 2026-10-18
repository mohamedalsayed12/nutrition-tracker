from flask import Blueprint, jsonify
from flask_jwt_extended import current_user, jwt_required
from sqlalchemy.exc import IntegrityError

from schemas import UserCreate, validate_body
from services.users import create_user, user_payload


router = Blueprint("users", __name__)


@router.post("")
@validate_body(UserCreate)
def create_user_route(data):
    try:
        return jsonify(create_user(data)), 201
    except IntegrityError:
        return jsonify(error="Email is already registered."), 409


@router.get("/me")
@jwt_required()
def get_user():
    return jsonify(user_payload(current_user))
