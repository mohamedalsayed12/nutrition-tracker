from flask import jsonify
from flask_jwt_extended import JWTManager, get_jwt_identity

from database import db
from models import User


jwt = JWTManager()


@jwt.user_lookup_loader
def load_token_user(_header, payload):
    identity = payload.get("sub")
    if not isinstance(identity, str) or not identity.isdecimal():
        return None
    return db.session.get(User, int(identity))


@jwt.user_lookup_error_loader
def missing_token_user(_header, _payload):
    return jsonify(error="User no longer exists."), 401


def current_user_id():
    return int(get_jwt_identity())
