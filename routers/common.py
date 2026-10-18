from flask import abort, jsonify, request

from database import db
from oauth2 import current_user_id
from schemas import Pagination


def owned_record(model, record_id):
    record = db.session.query(model).filter_by(id=record_id, user_id=current_user_id()).first()
    if record is None:
        abort(404, description="Record not found.")
    return record


def paginated(model, serialize):
    pagination = Pagination.model_validate(request.args.to_dict())
    query = db.session.query(model).filter_by(user_id=current_user_id())
    records = query.order_by(model.logged_at.desc(), model.id.desc()).offset(
        (pagination.page - 1) * pagination.per_page).limit(pagination.per_page).all()
    return jsonify(items=[serialize(record) for record in records], total=query.count(),
                   page=pagination.page, per_page=pagination.per_page)
