from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token

from database import db
from models import User
from schemas import UserLogin, validate_body
from utils import verify_password


router = Blueprint("auth", __name__)


@router.post("/login")
@validate_body(UserLogin)
def login(data):
    user = db.session.query(User).filter_by(email=str(data.email).lower()).first()
    if user is None or not verify_password(data.password, user.password):
        return jsonify(error="Invalid email or password."), 401
    return jsonify(access_token=create_access_token(identity=str(user.uid)), token_type="Bearer")
