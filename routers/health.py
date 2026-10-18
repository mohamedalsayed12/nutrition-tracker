from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from database import db
from services.openapi import api_specification


router = Blueprint("health", __name__)


@router.get("/api/v1/health")
def health():
    return jsonify(status="ok")


@router.get("/api/v1/ready")
def ready():
    db.session.execute(text("SELECT 1"))
    return jsonify(status="ready")


@router.get("/openapi.json")
def openapi():
    return jsonify(api_specification(current_app))
