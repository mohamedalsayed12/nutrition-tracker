from datetime import datetime, timezone
from decimal import Decimal

from flask import abort
from usda_fdc import FdcResourceNotFoundError

from database import db
from models import (ActivityLog, ExerciseDetails, ExerciseTargetCredit, FoodLog,
                    HealthPreferences, NutritionTargets, SavedEatingDay, UserActivityBaseline)
from services.calc import active_exercise_calories, scaled_food_nutrients
from services.exercise_ninjas import estimate_ninjas_calories
from services.food_search import get_food_client


def food_values(data):
    try:
        client = get_food_client()
    except ValueError as error:
        abort(503, description=str(error))
    try:
        food = client.get_food(data.fdc_id)
    except FdcResourceNotFoundError:
        abort(404, description="USDA food not found.")
    except Exception:
        abort(502, description="Food details are temporarily unavailable.")
    return dict(meal=data.meal, fdc_id=data.fdc_id, food_name=food.description,
                grams=data.grams, nutrients=scaled_food_nutrients(food, Decimal(str(data.grams))))


def invalidate_day(log):
    day = log.logged_at.date()
    saved = db.session.get(SavedEatingDay, (log.user_id, day))
    if saved is not None:
        db.session.delete(saved)


def create_food(user_id, data):
    log = FoodLog(user_id=user_id, logged_at=datetime.now(timezone.utc), **food_values(data))
    db.session.add(log)
    invalidate_day(log)
    db.session.commit()
    return log


def activity_values(user_id, data):
    nutrition = db.session.get(NutritionTargets, user_id)
    if nutrition is None:
        abort(409, description="Complete nutrition setup before logging exercise.")
    if data.extra and db.session.get(UserActivityBaseline, user_id) is None:
        abort(409, description="Set an activity baseline before adding exercise to your target.")
    preferences = db.session.get(HealthPreferences, user_id)
    if data.extra and preferences is not None and preferences.custom_calories is not None:
        abort(409, description="A fixed calorie target cannot receive exercise credit.")
    try:
        estimate = estimate_ninjas_calories(
            activity=data.activity,
            duration_minutes=data.duration_minutes,
            weight_kg=data.weight_kg,
            intensity=data.intensity,
            age=nutrition.age,
            sex=nutrition.sex,
            height_cm=data.height_cm,
        )
    except ValueError as error:
        abort(400, description=str(error))
    burned = estimate["calories_burned"]
    activity_type = estimate["activity_type"]
    return dict(
        activity=estimate["matched_name"] or data.activity,
        details=ExerciseDetails(
            duration_minutes=data.duration_minutes,
            calories_burned=burned,
            activity_type=activity_type,
            met=estimate["met"],
            height_cm=data.height_cm,
            weight_kg=data.weight_kg,
        ),
        target_credit=ExerciseTargetCredit(
            extra=data.extra,
            active_calories=active_exercise_calories(burned, activity_type),
        ),
        estimate=estimate,
    )


def create_activity(user_id, data):
    values = activity_values(user_id, data)
    log = ActivityLog(
        user_id=user_id,
        activity=values["activity"],
        details=values["details"],
        target_credit=values["target_credit"],
    )
    db.session.add(log)
    db.session.commit()
    return log


def update_activity(log, data):
    values = activity_values(log.user_id, data)
    log.activity = values["activity"]
    if log.details is None:
        log.details = values["details"]
    else:
        for field in ("duration_minutes", "calories_burned", "activity_type", "met", "height_cm", "weight_kg"):
            setattr(log.details, field, getattr(values["details"], field))
    if log.target_credit is None:
        log.target_credit = values["target_credit"]
    else:
        log.target_credit.extra = values["target_credit"].extra
        log.target_credit.active_calories = values["target_credit"].active_calories
    db.session.commit()
    return log


def serialize_food(log):
    return dict(id=log.id, meal=log.meal, fdc_id=log.fdc_id, food_name=log.food_name,
                grams=log.grams, nutrients=log.nutrients, logged_at=iso_utc(log.logged_at))


_ACTIVITY_TYPE_TO_INTENSITY = {
    "other_light": "easy",
    "other_moderate": "medium",
    "other_vigorous": "hard",
    "walking": "easy",
    "yoga": "easy",
    "strength": "medium",
    "cycling": "medium",
    "swimming": "medium",
    "running": "hard",
}


def serialize_activity(log):
    activity_type = log.details.activity_type if log.details else None
    return dict(
        id=log.id, activity=log.activity, logged_at=iso_utc(log.logged_at),
        duration_minutes=log.details.duration_minutes if log.details else None,
        calories_burned=log.details.calories_burned if log.details else None,
        activity_type=activity_type,
        intensity=_ACTIVITY_TYPE_TO_INTENSITY.get(activity_type),
        extra=log.target_credit.extra if log.target_credit else False,
    )


def iso_utc(value):
    return value.replace(tzinfo=value.tzinfo or timezone.utc).astimezone(timezone.utc).isoformat()
