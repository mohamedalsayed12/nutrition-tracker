from flask import Blueprint, current_app, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import db
from services.openapi import api_specification


router = Blueprint("health", __name__)


@router.get("/api/v1/health")
def health():
    return jsonify(status="ok")


@router.get("/api/v1/ready")
def ready():
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(status="unavailable", error="Database is not reachable."), 503
    return jsonify(status="ready")


@router.get("/openapi.json")
def openapi():
    return jsonify(api_specification(current_app))
