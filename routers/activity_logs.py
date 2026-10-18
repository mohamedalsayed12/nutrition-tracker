from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from database import db
from models import ActivityLog
from oauth2 import current_user_id
from routers.common import owned_record, paginated
from schemas import ActivityLogCreate, validate_body
from services.logs import create_activity, serialize_activity, update_activity


router = Blueprint("activity_logs", __name__)


@router.get("")
@jwt_required()
def list_activity_logs():
    return paginated(ActivityLog, serialize_activity)


@router.post("")
@jwt_required()
@validate_body(ActivityLogCreate)
def create_activity_log(data):
    return jsonify(serialize_activity(create_activity(current_user_id(), data))), 201


@router.get("/<int:log_id>")
@jwt_required()
def get_activity_log(log_id):
    return jsonify(serialize_activity(owned_record(ActivityLog, log_id)))


@router.delete("/<int:log_id>")
@jwt_required()
def delete_activity_log(log_id):
    db.session.delete(owned_record(ActivityLog, log_id))
    db.session.commit()
    return "", 204


@router.put("/<int:log_id>")
@jwt_required()
@validate_body(ActivityLogCreate)
def update_activity_log(log_id, data):
    return jsonify(serialize_activity(update_activity(owned_record(ActivityLog, log_id), data)))
