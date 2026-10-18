from datetime import datetime, timezone

from flask import abort

from database import db
from models import ConditionDayLog, HealthPreferences, NutritionTargets
from services.nutrient_targets import condition_micronutrient_guidance


def _require_nutrition(user_id):
    nutrition = db.session.get(NutritionTargets, user_id)
    if nutrition is None:
        abort(409, description="Complete nutrition setup first.")
    return nutrition


def validate_day_conditions(user_id, conditions):
    nutrition = _require_nutrition(user_id)
    conditions = sorted(set(conditions or []))
    if "menstruation" in conditions and nutrition.sex != "female":
        raise ValueError("Period logging is available when nutrition sex is set to female.")
    preferences = db.session.get(HealthPreferences, user_id)
    preference_conditions = set(preferences.conditions or []) if preferences else set()
    if "menstruation" in conditions and "pregnancy" in preference_conditions:
        raise ValueError("Pregnancy and menstruation cannot both be active.")
    if "pregnancy" in conditions:
        raise ValueError("Log pregnancy in health settings, not as a day condition.")
    return conditions


def get_day_conditions(user_id, day):
    _require_nutrition(user_id)
    entry = db.session.get(ConditionDayLog, (user_id, day))
    conditions = list(entry.conditions or []) if entry else []
    return dict(
        date=day.isoformat(),
        conditions=conditions,
        guidance=condition_micronutrient_guidance(conditions),
    )


def set_day_conditions(user_id, day, data):
    conditions = validate_day_conditions(user_id, data.conditions)
    entry = db.session.get(ConditionDayLog, (user_id, day))
    if not conditions:
        if entry is not None:
            db.session.delete(entry)
            db.session.commit()
        return get_day_conditions(user_id, day)
    if entry is None:
        entry = ConditionDayLog(user_id=user_id, day=day, conditions=conditions)
        db.session.add(entry)
    else:
        entry.conditions = conditions
        entry.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return get_day_conditions(user_id, day)


def clear_day_conditions(user_id, day):
    _require_nutrition(user_id)
    entry = db.session.get(ConditionDayLog, (user_id, day))
    if entry is not None:
        db.session.delete(entry)
        db.session.commit()
    return get_day_conditions(user_id, day)


def day_condition_list(user_id, day):
    entry = db.session.get(ConditionDayLog, (user_id, day))
    return list(entry.conditions or []) if entry else []
