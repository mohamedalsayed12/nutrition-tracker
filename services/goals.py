from datetime import datetime, timezone

from database import db, save_calorie_target
from models import HealthPreferences, NutritionTargets, UserActivityBaseline, UserMeasurements
from services.calc import (UserInfo, apply_health_preferences, calculate_goal_targets,
                           configured_micronutrients, validate_care_plan_macros)


def set_nutrition_goals(user_id, data):
    age, sex = data.age, data.sex
    height, weight = data.height_cm, data.weight_kg
    activity_level, goal = data.activity_level, data.goal
    preferences = db.session.get(HealthPreferences, user_id)
    info = UserInfo()
    info.func(age=age, gender=sex, height=height, weight=weight, activity_level=activity_level)
    pregnancy_active = preferences is not None and "pregnancy" in (preferences.conditions or [])
    try:
        bmr, tdee, calories, protein_min, protein_max, carbs = calculate_goal_targets(info, goal, pregnancy_active)
        nutrition = db.session.get(NutritionTargets, user_id)
        if nutrition is None:
            nutrition = NutritionTargets(user_id=user_id)
            db.session.add(nutrition)
        nutrition.age = age
        nutrition.sex = sex
        nutrition.protein_min = protein_min
        nutrition.protein_max = protein_max
        nutrition.carbs = carbs
        nutrition.micronutrients = configured_micronutrients(age, sex, preferences)
        measurements = db.session.get(UserMeasurements, user_id)
        if measurements is None:
            measurements = UserMeasurements(user_id=user_id)
            db.session.add(measurements)
        measurements.height_cm = height
        measurements.weight_kg = weight
        baseline = db.session.get(UserActivityBaseline, user_id)
        if baseline is None:
            baseline = UserActivityBaseline(user_id=user_id)
            db.session.add(baseline)
        elif baseline.activity_level != activity_level:
            baseline.changed_at = datetime.now(timezone.utc)
        baseline.activity_level = activity_level
        if preferences is not None:
            preferences.base_calories = calories
            preferences.base_carbs = carbs
            preferences.base_protein_min = protein_min
            preferences.base_protein_max = protein_max
            effective_calories = apply_health_preferences(nutrition, preferences)
            validate_care_plan_macros(effective_calories, preferences)
        else:
            effective_calories = calories
        save_calorie_target(user_id, effective_calories)
        db.session.commit()
    except ValueError:
        db.session.rollback()
        raise
    return dict(
        bmr=bmr, tdee=tdee, calories=effective_calories,
        protein_min=nutrition.protein_min, protein_max=nutrition.protein_max,
        carbs=nutrition.carbs, micronutrients=nutrition.micronutrients,
    )
