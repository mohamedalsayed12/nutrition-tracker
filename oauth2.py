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


# Flask-JWT-Extended answers a malformed or badly signed token with 422 by
# default. An unusable token is an authentication failure, so return 401 and
# keep every auth error in the same {"error": ...} shape as the rest of the API.
@jwt.invalid_token_loader
def invalid_token(_reason):
    return jsonify(error="Invalid access token."), 401


@jwt.unauthorized_loader
def missing_token(_reason):
    return jsonify(error="Missing access token."), 401


@jwt.expired_token_loader
def expired_token(_header, _payload):
    return jsonify(error="Access token has expired."), 401


def current_user_id():
    return int(get_jwt_identity())
