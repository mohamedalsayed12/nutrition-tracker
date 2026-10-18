from flask import abort

from database import db, save_calorie_target
from models import CalorieTarget, HealthPreferences, MacroSplit, NutritionTargets
from services.calc import apply_health_preferences, validate_care_plan_macros
from services.nutrient_targets import micronutrient_targets


def require_nutrition(user_id):
    nutrition = db.session.get(NutritionTargets, user_id)
    if nutrition is None:
        abort(409, description="Complete nutrition setup first.")
    return nutrition


def set_calories(user_id, calories):
    preferences = db.session.get(HealthPreferences, user_id)
    if preferences is not None:
        preferences.custom_calories = calories
        nutrition = require_nutrition(user_id)
        apply_health_preferences(nutrition, preferences)
        validate_care_plan_macros(calories, preferences)
    save_calorie_target(user_id, calories)
    db.session.commit()
    return dict(calories=calories)


def set_health_settings(user_id, data):
    nutrition = require_nutrition(user_id)
    if "menstruation" in data.conditions and nutrition.sex != "female":
        raise ValueError("Menstruation is available when nutrition sex is female.")
    targets = micronutrient_targets(nutrition.age, nutrition.sex, pregnant="pregnancy" in data.conditions)
    allowed = {target["name"] for target in targets}
    if not set(data.micronutrient_overrides).issubset(allowed):
        raise ValueError("Unknown micronutrient override.")
    preferences = db.session.get(HealthPreferences, user_id)
    if preferences is None:
        target = db.session.get(CalorieTarget, user_id)
        preferences = HealthPreferences(user_id=user_id, base_calories=target.calories if target else None,
                                        base_carbs=nutrition.carbs, base_protein_min=nutrition.protein_min,
                                        base_protein_max=nutrition.protein_max)
        db.session.add(preferences)
    for name, value in data.model_dump().items():
        setattr(preferences, name, value)
    preferences.conditions = sorted(set(data.conditions))
    # apply_health_preferences → configured_micronutrients applies menstruation
    # iron / vitamin C bumps (and pregnancy references) onto stored targets.
    calories = apply_health_preferences(nutrition, preferences)
    validate_care_plan_macros(calories, preferences)
    save_calorie_target(user_id, calories)
    db.session.commit()
    return preferences


def set_macro_split(user_id, data):
    require_nutrition(user_id)
    split = db.session.get(MacroSplit, user_id)
    if split is None:
        split = MacroSplit(user_id=user_id)
        db.session.add(split)
    for name, value in data.model_dump().items():
        setattr(split, name, value)
    db.session.commit()
    return data.model_dump()
