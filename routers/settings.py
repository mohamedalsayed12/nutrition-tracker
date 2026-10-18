from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from database import db
from models import HealthPreferences, MacroSplit
from oauth2 import current_user_id
from schemas import HealthSettings, MacroSplitInput, validate_body
from services.nutrient_targets import condition_micronutrient_guidance
from services.settings import set_health_settings, set_macro_split


router = Blueprint("settings", __name__)


def health_response(preferences):
    fields = HealthSettings.model_fields
    values = {name: getattr(preferences, name) for name in fields} if preferences else HealthSettings().model_dump()
    return dict(**values, guidance=condition_micronutrient_guidance(values["conditions"]))


@router.get("/health")
@jwt_required()
def health_settings():
    return jsonify(health_response(db.session.get(HealthPreferences, current_user_id())))


@router.put("/health")
@jwt_required()
@validate_body(HealthSettings)
def update_health_settings(data):
    return jsonify(health_response(set_health_settings(current_user_id(), data)))


@router.get("/macro-split")
@jwt_required()
def macro_split():
    split = db.session.get(MacroSplit, current_user_id())
    return jsonify(configured=split is not None, **{
        field: getattr(split, field) if split else default
        for field, default in (("carbs_percent", 55), ("protein_percent", 20), ("fat_percent", 25))
    })


@router.put("/macro-split")
@jwt_required()
@validate_body(MacroSplitInput)
def update_macro_split(data):
    return jsonify(set_macro_split(current_user_id(), data))


@router.delete("/macro-split")
@jwt_required()
def reset_macro_split():
    split = db.session.get(MacroSplit, current_user_id())
    if split is not None:
        db.session.delete(split)
        db.session.commit()
    return "", 204
