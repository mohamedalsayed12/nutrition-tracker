from datetime import datetime

from flask import Blueprint, abort, g, jsonify
from flask_jwt_extended import jwt_required

from database import db
from models import ApiToken
from oauth2 import current_user_id
from routers.common import owned_record
from schemas import ApiTokenCreate, VoiceLogCreate, validate_body
from services.api_tokens import api_token_required, create_token, serialize_token
from services.food_search import get_food_client
from services.reports import daily_report, report_timezone
from services.voice_log import log_spoken_meal, spoken_reply


router = Blueprint("voice", __name__)


@router.get("/api-tokens")
@jwt_required()
def list_tokens():
    tokens = db.session.query(ApiToken).filter_by(user_id=current_user_id()).order_by(ApiToken.created_at).all()
    return jsonify(tokens=[serialize_token(token) for token in tokens])


@router.post("/api-tokens")
@jwt_required()
@validate_body(ApiTokenCreate)
def new_token(data):
    try:
        report_timezone(data.timezone)
    except ValueError as error:
        abort(422, description=str(error))
    token, key = create_token(current_user_id(), data.name, data.timezone)
    return jsonify(dict(serialize_token(token), key=key)), 201


@router.delete("/api-tokens/<int:token_id>")
@jwt_required()
def delete_token(token_id):
    db.session.delete(owned_record(ApiToken, token_id))
    db.session.commit()
    return "", 204


@router.post("/voice-log")
@api_token_required
@validate_body(VoiceLogCreate)
def voice_log(data):
    """Log what was said to Siri. Called by the iPhone Shortcut with a Siri key."""
    token = g.api_token
    zone = report_timezone(token.timezone)
    try:
        client = get_food_client()
    except ValueError as error:
        abort(503, description=str(error))
    meal, logged, not_found = log_spoken_meal(token.user_id, data.text, zone, client, meal=data.meal)
    report = daily_report(token.user_id, datetime.now(zone).date(), zone)
    goal = report["calorie_goal"]
    eaten = report["totals"]["Calories"]
    left = round(goal - eaten, 1) if goal is not None else None
    db.session.commit()
    return jsonify(meal=meal, logged=logged, not_found=not_found,
                   calories_today=round(eaten), calorie_target=goal, calories_left=left,
                   spoken=spoken_reply(meal, logged, not_found, left)), 201 if logged else 200
