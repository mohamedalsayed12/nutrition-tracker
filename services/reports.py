from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from database import db
from models import ActivityLog, CalorieTarget, FoodLog, HealthPreferences, MacroSplit, NutritionTargets, UserActivityBaseline
from services.calc import (condition_nutrition_data, configured_micronutrients,
                           daily_target_progress, frequent_food_choices)
from services.nutrient_scoring import remaining_targets
from services.weekly_recap import build_weekly_recap, food_macros
from services.logs import iso_utc


def report_timezone(name):
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("Choose a valid IANA timezone.") from None


def as_utc(value):
    return value.replace(tzinfo=value.tzinfo or timezone.utc).astimezone(timezone.utc)


def day_range(day, zone):
    start = datetime.combine(day, time.min, zone)
    return start.astimezone(timezone.utc), (start + timedelta(days=1)).astimezone(timezone.utc)


def daily_report(user_id, day, zone):
    start, end = day_range(day, zone)
    foods = db.session.query(FoodLog).filter(FoodLog.user_id == user_id, FoodLog.logged_at >= start, FoodLog.logged_at < end).all()
    activities = db.session.query(ActivityLog).filter(ActivityLog.user_id == user_id, ActivityLog.logged_at >= start, ActivityLog.logged_at < end).all()
    target = db.session.get(CalorieTarget, user_id)
    nutrition = db.session.get(NutritionTargets, user_id)
    preferences = db.session.get(HealthPreferences, user_id)
    baseline = db.session.get(UserActivityBaseline, user_id)
    split = db.session.get(MacroSplit, user_id)
    credit = 0
    if baseline is not None and not (preferences and preferences.custom_calories is not None):
        credit = round(sum(log.target_credit.active_calories for log in activities
                           if log.target_credit is not None and log.target_credit.extra
                           and as_utc(log.logged_at) >= as_utc(baseline.changed_at)), 1)
    calories = round(target.calories + credit, 1) if target else None
    progress, fat_range, custom_macros, protein_min, protein_max, carbs = daily_target_progress(
        foods, calories, credit, nutrition, split, preferences)
    totals = {name: 0.0 for name in ("Calories", "Protein", "Carbohydrates", "Fat")}
    reported = {name: 0 for name in totals}
    for log in foods:
        for name, value in food_macros(log.nutrients).items():
            totals[name] += value
            reported[name] += 1
    micronutrients = configured_micronutrients(nutrition.age, nutrition.sex, preferences) if nutrition else []
    return dict(date=day.isoformat(), timezone=str(zone), food_log_count=len(foods),
                totals={name: round(value, 2) for name, value in totals.items()}, reported=reported,
                calorie_goal=calories, exercise_credit=credit, progress=progress, fat_range=fat_range,
                custom_macros=custom_macros, protein_min=protein_min, protein_max=protein_max, carbs=carbs,
                micronutrients=remaining_targets(foods, micronutrients),
                condition_nutrition=condition_nutrition_data(foods, calories))


def weekly_report(user_id, week_start, zone):
    start, _ = day_range(week_start, zone)
    _, end = day_range(week_start + timedelta(days=6), zone)
    foods = db.session.query(FoodLog).filter(FoodLog.user_id == user_id, FoodLog.logged_at >= start, FoodLog.logged_at < end).all()
    nutrition = db.session.get(NutritionTargets, user_id)
    preferences = db.session.get(HealthPreferences, user_id)
    targets = configured_micronutrients(nutrition.age, nutrition.sex, preferences) if nutrition else []
    return dict(week_start=week_start.isoformat(), timezone=str(zone),
                **build_weekly_recap(foods, zone, week_start, targets))


def frequent_foods(user_id):
    foods = db.session.query(FoodLog).filter_by(user_id=user_id).order_by(FoodLog.logged_at.desc()).all()
    choices = frequent_food_choices(foods)
    for items in choices.values():
        for item in items:
            item["last_logged"] = iso_utc(item["last_logged"])
    return choices
