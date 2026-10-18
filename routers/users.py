from flask import Blueprint, jsonify
from flask_jwt_extended import current_user, jwt_required
from sqlalchemy.exc import IntegrityError

from database import db
from models import User
from schemas import UserCreate, validate_body
from utils import hash_password


router = Blueprint("users", __name__)


@router.post("")
@validate_body(UserCreate)
def create_user(data):
    user = User(username=data.name, email=str(data.email), password=hash_password(data.password))
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="Email is already registered."), 409
    return jsonify(id=user.uid, name=user.username, email=user.email), 201


@router.get("/me")
@jwt_required()
def get_user():
    return jsonify(id=current_user.uid, name=current_user.username, email=current_user.email)
