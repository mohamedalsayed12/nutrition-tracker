import math
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import unquote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user
from flask_wtf import FlaskForm
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired

from database import db
from models import (ActivityLog, CalorieTarget, ExerciseDetails, ExerciseTargetCredit,
                    FoodLog, HealthPreferences, MacroSplit, MealSubmission, NutritionTargets,
                    SavedEatingDay, User, UserActivityBaseline, UserMeasurements)
from schemas import HealthSettings, MacroSplitInput, NutritionSetup, UserCreate
from services.calc import (EXERCISE_METS, UserInfo, active_exercise_calories,
                           calculate_goal_targets, condition_nutrition_data,
                           configured_micronutrients, custom_macro_targets,
                           daily_target_progress, estimate_exercise_calories,
                           exercise_adjusted_target, fat_target_range, frequent_food_choices,
                           grams_for_measure, scaled_food_nutrients, weekly_target_labels)
from services.food_search import get_food_client
from services.goals import set_nutrition_goals
from services.nutrient_scoring import npc_rating, nutrient_per_100_calories, remaining_targets
from services.nutrient_targets import condition_micronutrient_guidance, micronutrient_targets
from services.settings import set_health_settings, set_macro_split
from services.weekly_recap import build_weekly_recap
from utils import hash_password, verify_password


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


def register_pages(app):
    app.add_url_rule("/", endpoint="root", view_func=root)
    app.add_url_rule("/login", endpoint="auth.login_page", view_func=login_page, methods=["GET", "POST"])
    app.add_url_rule("/register", endpoint="auth.registration_page", view_func=registration_page, methods=["GET", "POST"])
    app.add_url_rule("/homepage", endpoint="home_page", view_func=home_page, methods=["GET", "POST"])
    app.add_url_rule("/UserInfo", endpoint="user_info_page", view_func=user_info_page, methods=["GET", "POST"])
    app.add_url_rule("/macro-split", endpoint="macro_split_settings", view_func=macro_split_settings, methods=["GET", "POST"])
    app.add_url_rule("/health-settings", endpoint="health_settings", view_func=health_settings, methods=["GET", "POST"])
    app.add_url_rule("/weekly-recap", endpoint="weekly_recap_page", view_func=weekly_recap_page)
    app.add_url_rule("/days/save", endpoint="save_eating_day", view_func=save_eating_day, methods=["POST"])
    app.add_url_rule("/logs/food/<int:log_id>/delete", endpoint="delete_food_log", view_func=delete_food_log, methods=["POST"])
    app.add_url_rule("/logs/activity/<int:log_id>/delete", endpoint="delete_activity_log", view_func=delete_activity_log, methods=["POST"])


def root():
    return redirect(url_for("home_page"))


def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.email.data.strip().lower()).first()
        if user is None or not verify_password(form.password.data, user.password):
            return render_template("login.html", form=form, erorr="Invalid email or password.")
        login_user(user, remember=bool(form.remember.data))
        flash("Logged in successful.")
        return redirect(url_for("home_page"))
    if request.method == "POST":
        return render_template("login.html", form=form, erorr="Invalid form. Refresh and try again."), 400
    return render_template("login.html", form=form)


def registration_page():
    form = RegistrationForm()
    if request.method == "POST":
        if not form.validate_on_submit():
            return render_template("register.html", form=form, error="Invalid form. Refresh and try again."), 400
        try:
            data = UserCreate(name=form.name.data, email=form.email.data, password=form.password.data)
        except ValidationError as exc:
            return render_template("register.html", form=form, error=_validation_message(exc)), 400
        if db.session.query(User).filter_by(email=str(data.email)).first() is not None:
            return render_template("register.html", form=form, error="Email is already registered."), 409
        db.session.add(User(username=data.name, email=str(data.email), password=hash_password(data.password)))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render_template("register.html", form=form, error="Email is already registered."), 409
        return redirect(url_for("auth.login_page"))
    return render_template("register.html", form=form)


@login_required
def user_info_page():
    bmr = tdee = calories_for_goal = protein_min = protein_max = carbs = error = None
    micronutrients = info = None
    preferences = db.session.get(HealthPreferences, current_user.uid)
    macro_split = db.session.get(MacroSplit, current_user.uid)
    pregnancy_active = preferences is not None and "pregnancy" in (preferences.conditions or [])
    if request.method == "POST":
        try:
            payload = NutritionSetup(
                age=int(request.form["age"]), sex=request.form["gender"],
                height_cm=float(request.form["height"]), weight_kg=float(request.form["weight"]),
                activity_level=request.form["activity_level"], goal=request.form["goal"],
            )
            info = UserInfo()
            info.func(age=payload.age, gender=payload.sex, height=payload.height_cm,
                      weight=payload.weight_kg, activity_level=payload.activity_level)
            bmr, tdee, calories_for_goal, protein_min, protein_max, carbs = calculate_goal_targets(
                info, payload.goal, pregnancy_active)
            result = set_nutrition_goals(current_user.uid, payload)
            micronutrients = result["micronutrients"]
        except (KeyError, TypeError, ValueError, InvalidOperation, ValidationError) as exc:
            db.session.rollback()
            error = "Enter every field." if isinstance(exc, KeyError) else _validation_message(exc)
            calories_for_goal = protein_min = protein_max = carbs = micronutrients = None
    return render_template(
        "user_info.html", bmr=bmr, tdee=tdee, error=error,
        values=request.form, calories_for_goal=calories_for_goal,
        protein_min=protein_min, protein_max=protein_max, carbs=carbs,
        fat_range=fat_target_range(calories_for_goal, info.age) if calories_for_goal is not None and info is not None else None,
        macro_split=macro_split,
        custom_macros=custom_macro_targets(calories_for_goal, macro_split, preferences) if calories_for_goal is not None else None,
        micronutrients=micronutrients, pregnancy_active=pregnancy_active,
    )


@login_required
def macro_split_settings():
    if db.session.get(NutritionTargets, current_user.uid) is None:
        return redirect(url_for("user_info_page"))
    split = db.session.get(MacroSplit, current_user.uid)
    error = None
    token = _ensure_token("_macro_token")
    if request.method == "POST":
        _require_token("_macro_token", "_macro_token")
        try:
            action = request.form.get("action", "save")
            if action == "default":
                if split is not None:
                    db.session.delete(split)
                    db.session.commit()
            elif action == "save":
                percentages = {}
                for name in ("carbs", "protein", "fat"):
                    value = Decimal(request.form[f"{name}_percent"])
                    if not value.is_finite() or value < 0 or value > 100:
                        raise ValueError("Each percentage must be between 0 and 100.")
                    percentages[name] = value
                if sum(percentages.values()) != 100:
                    raise ValueError("Carbohydrates, protein, and fat must add up to 100%.")
                set_macro_split(current_user.uid, MacroSplitInput(
                    carbs_percent=float(percentages["carbs"]),
                    protein_percent=float(percentages["protein"]),
                    fat_percent=float(percentages["fat"]),
                ))
            else:
                raise ValueError("Choose a valid macro split action.")
            return redirect(url_for("home_page"))
        except (KeyError, ValueError, InvalidOperation, ValidationError) as exc:
            db.session.rollback()
            error = "Enter all three percentages." if isinstance(exc, KeyError) else _validation_message(exc)
    values = {
        name: request.form.get(f"{name}_percent", "") if request.method == "POST"
        else getattr(split, f"{name}_percent") if split is not None
        else default
        for name, default in (("carbs", 55), ("protein", 20), ("fat", 25))
    }
    preferences = db.session.get(HealthPreferences, current_user.uid)
    target = db.session.get(CalorieTarget, current_user.uid)
    return render_template(
        "macro_split.html", values=values, error=error, token=token, split=split,
        calorie_target=target.calories if target is not None else None,
        overridden_macros=[name for name, field in (("carbohydrate", "custom_carbs"),
                                                  ("protein", "custom_protein"),
                                                  ("fat", "custom_fat"))
                           if preferences is not None and getattr(preferences, field) is not None],
    )


@login_required
def health_settings():
    nutrition = db.session.get(NutritionTargets, current_user.uid)
    if nutrition is None:
        return redirect(url_for("user_info_page"))
    preferences = db.session.get(HealthPreferences, current_user.uid)
    error = None
    token = _ensure_token("_health_token")
    if request.method == "POST":
        _require_token("_health_token", "_health_token")
        try:
            conditions = set(request.form.getlist("conditions"))
            if not conditions.issubset({"pregnancy", "diabetes", "ibs", "menstruation"}):
                raise ValueError("Choose a listed medical condition.")
            pregnant = "pregnancy" in conditions
            trimester = int(request.form.get("trimester", "")) if pregnant else None
            overrides = {}
            base_targets = micronutrient_targets(nutrition.age, nutrition.sex, pregnant=pregnant)
            for index, target in enumerate(base_targets):
                amount = _optional_positive_number(f"micro_{index}", 1000000)
                if amount is not None:
                    overrides[target["name"]] = amount
            set_health_settings(current_user.uid, HealthSettings(
                conditions=sorted(conditions), trimester=trimester,
                custom_calories=_care_plan_calories(),
                custom_carbs=_optional_positive_number("custom_carbs", 1500),
                custom_protein=_optional_positive_number("custom_protein", 1500),
                custom_fat=_optional_positive_number("custom_fat", 1500),
                micronutrient_overrides=overrides,
            ))
            return redirect(url_for("health_settings"))
        except (ValueError, TypeError, InvalidOperation, ValidationError) as exc:
            db.session.rollback()
            error = _validation_message(exc)
    selected = (request.form.getlist("conditions") if request.method == "POST" else
                (preferences.conditions or []) if preferences is not None else [])
    pregnant = "pregnancy" in selected and 14 <= nutrition.age <= 50
    base_targets = micronutrient_targets(nutrition.age, nutrition.sex, pregnant=pregnant)
    saved_overrides = (preferences.micronutrient_overrides or {}) if preferences is not None else {}
    rows = [dict(target, index=index,
                 override=(request.form.get(f"micro_{index}", "") if request.method == "POST"
                           else saved_overrides.get(target["name"], "")))
            for index, target in enumerate(base_targets)]
    return render_template(
        "health_settings.html", error=error, rows=rows, selected=selected,
        trimester=(request.form.get("trimester", "") if request.method == "POST"
                   else preferences.trimester if preferences is not None else ""),
        custom_calories=(request.form.get("custom_calories", "") if request.method == "POST"
                         else preferences.custom_calories if preferences is not None else ""),
        custom_carbs=(request.form.get("custom_carbs", "") if request.method == "POST"
                      else preferences.custom_carbs if preferences is not None else ""),
        custom_protein=(request.form.get("custom_protein", "") if request.method == "POST"
                        else preferences.custom_protein if preferences is not None else ""),
        custom_fat=(request.form.get("custom_fat", "") if request.method == "POST"
                    else preferences.custom_fat if preferences is not None else ""),
        token=token, age=nutrition.age, sex=nutrition.sex,
        condition_guidance=condition_micronutrient_guidance(selected),
    )


@login_required
def weekly_recap_page():
    local_timezone = _user_timezone()
    today = datetime.now(local_timezone).date()
    current_week_start = today - timedelta(days=today.weekday())
    requested = request.args.get("week", "")
    try:
        selected_day = date.fromisoformat(requested) if requested else today
    except ValueError:
        abort(400)
    week_start = selected_day - timedelta(days=selected_day.weekday())
    if week_start > current_week_start:
        return redirect(url_for("weekly_recap_page"))
    week_end = week_start + timedelta(days=6)
    nutrition = db.session.get(NutritionTargets, current_user.uid)
    preferences = db.session.get(HealthPreferences, current_user.uid)
    split = db.session.get(MacroSplit, current_user.uid)
    target = db.session.get(CalorieTarget, current_user.uid)
    micronutrients = (configured_micronutrients(nutrition.age, nutrition.sex, preferences)
                      if nutrition is not None else [])
    food_logs = _food_logs(current_user.uid)
    return render_template(
        "weekly_recap.html",
        recap=build_weekly_recap(food_logs, local_timezone, week_start, micronutrients),
        week_start=week_start, week_end=week_end,
        previous_week=(week_start - timedelta(days=7)).isoformat(),
        next_week=(week_start + timedelta(days=7)).isoformat() if week_start < current_week_start else None,
        saved_count=_saved_days_count(current_user.uid, week_start, week_end),
        target_labels=weekly_target_labels(target.calories if target is not None else None, nutrition, split, preferences),
    )


@login_required
def save_eating_day():
    _require_token("_save_day_token", "_save_day_token")
    try:
        day = date.fromisoformat(request.form.get("day", ""))
    except ValueError:
        abort(400)
    local_timezone = _user_timezone()
    if day > datetime.now(local_timezone).date():
        abort(400)
    foods = _food_logs(current_user.uid)
    if not any(_local_day(food.logged_at, local_timezone) == day for food in foods):
        flash("Log at least one food for that day before saving it.")
        return redirect(url_for("home_page"))
    if db.session.get(SavedEatingDay, (current_user.uid, day)) is None:
        db.session.add(SavedEatingDay(user_id=current_user.uid, day=day))
        db.session.commit()
    flash("Day of eating saved.")
    return redirect(url_for("home_page"))


@login_required
def delete_food_log(log_id):
    _require_token("_delete_token", "_delete_token")
    local_timezone = _user_timezone()
    log = db.session.get(FoodLog, log_id)
    if log is None or log.user_id != current_user.uid:
        abort(404)
    matching = (db.session.query(FoodLog)
                .filter_by(user_id=current_user.uid, meal=log.meal, fdc_id=log.fdc_id, grams=log.grams)
                .order_by(FoodLog.logged_at.desc(), FoodLog.id.desc()).all())
    clusters = []
    previous = None
    for entry in matching:
        if (previous is None or _local_day(entry.logged_at, local_timezone) != _local_day(previous.logged_at, local_timezone)
                or (_as_utc(previous.logged_at) - _as_utc(entry.logged_at)).total_seconds() >= 5):
            clusters.append([])
        clusters[-1].append(entry)
        previous = entry
    for cluster in clusters:
        if any(entry.id == log_id for entry in cluster):
            changed_days = {_local_day(entry.logged_at, local_timezone) for entry in cluster}
            for entry in cluster:
                db.session.delete(entry)
            _reopen_eating_days(current_user.uid, changed_days)
            break
    db.session.commit()
    return redirect(url_for("home_page"))


@login_required
def delete_activity_log(log_id):
    _require_token("_delete_token", "_delete_token")
    log = db.session.get(ActivityLog, log_id)
    if log is None or log.user_id != current_user.uid:
        abort(404)
    db.session.delete(log)
    db.session.commit()
    return redirect(url_for("home_page"))


@login_required
def home_page():
    error = None
    local_timezone = _user_timezone()
    measurements = db.session.get(UserMeasurements, current_user.uid)
    activity_baseline = db.session.get(UserActivityBaseline, current_user.uid)
    preferences = db.session.get(HealthPreferences, current_user.uid)
    fixed_care_plan_target = preferences is not None and preferences.custom_calories is not None
    submission_token = request.form.get("_submission_token") or secrets.token_urlsafe(32)

    if request.method == "POST":
        try:
            db.session.add(MealSubmission(user_id=current_user.uid, token=submission_token))
            has_food = any(request.form.get(meal, "").strip() for meal in ("breakfast", "lunch", "dinner"))
            activity = request.form.get("activity", "").strip()
            if not has_food and not activity:
                raise ValueError("Choose a food or enter an exercise to save.")
            client = get_food_client() if has_food else None
            new_food_logs = []
            for meal in ("breakfast", "lunch", "dinner"):
                selection = request.form.get(meal, "").strip()
                if not selection:
                    continue
                match = re.fullmatch(r".+ \[FDC:(\d+)\]", selection)
                if not match:
                    raise ValueError(f"Please select a {meal} food from the suggestions.")
                food = client.get_food(int(match.group(1)))
                measure = request.form.get(f"{meal}_measure", "").strip()
                if measure:
                    grams = grams_for_measure(food, Decimal(request.form.get(f"{meal}_amount", "")), measure)
                else:
                    grams = Decimal(request.form.get(f"{meal}_grams", "").strip())
                    if not grams.is_finite() or grams <= 0:
                        raise ValueError(f"Enter a positive gram amount for {meal}.")
                new_food_logs.append(FoodLog(
                    user_id=current_user.uid, meal=meal, fdc_id=int(match.group(1)),
                    food_name=food.description, grams=float(grams),
                    nutrients=scaled_food_nutrients(food, grams),
                    logged_at=datetime.now(timezone.utc),
                ))
            for log in new_food_logs:
                db.session.add(log)
            if new_food_logs:
                _reopen_eating_days(current_user.uid, {
                    _local_day(log.logged_at, local_timezone) for log in new_food_logs
                })
            if activity:
                _add_activity(activity, activity_baseline, fixed_care_plan_target, measurements)
            db.session.commit()
            return redirect(url_for("home_page"))
        except IntegrityError:
            db.session.rollback()
            if db.session.get(MealSubmission, (current_user.uid, submission_token)) is not None:
                return redirect(url_for("home_page"))
            error = "Could not save the meal. Please try again."
        except (ValueError, InvalidOperation, ValidationError) as exc:
            db.session.rollback()
            error = _validation_message(exc)
        except Exception:
            db.session.rollback()
            error = "Could not retrieve or save the food details. Please try again."

    all_food_logs = _food_logs(current_user.uid, newest_first=True)
    frequent_foods = frequent_food_choices(all_food_logs)
    last_seen = {}
    meal_groups = {}
    for log in all_food_logs:
        day = _local_day(log.logged_at, local_timezone)
        duplicate_key = (day, log.meal, log.fdc_id, log.grams)
        previous = last_seen.get(duplicate_key)
        last_seen[duplicate_key] = log.logged_at
        if previous is not None and (_as_utc(previous) - _as_utc(log.logged_at)).total_seconds() < 5:
            continue
        group = meal_groups.setdefault((day, log.meal), {"date": day, "meal": log.meal, "foods": []})
        group["foods"].append(log)
    activity_logs = (db.session.query(ActivityLog).filter_by(user_id=current_user.uid)
                     .order_by(ActivityLog.logged_at.desc()).all())
    for log in activity_logs:
        log.local_date = _local_day(log.logged_at, local_timezone)
    target = db.session.get(CalorieTarget, current_user.uid)
    nutrition = db.session.get(NutritionTargets, current_user.uid)
    macro_split = db.session.get(MacroSplit, current_user.uid)
    if nutrition is not None:
        current_micronutrients = configured_micronutrients(nutrition.age, nutrition.sex, preferences)
        if nutrition.micronutrients != current_micronutrients:
            nutrition.micronutrients = current_micronutrients
            db.session.commit()
    today = datetime.now(local_timezone).date()
    exercise_credit_today, daily_calorie_target = exercise_adjusted_target(
        target, activity_logs, today, activity_baseline, fixed_care_plan_target)
    today_food_logs = []
    for group in meal_groups.values():
        for log in group["foods"]:
            log.npc_result = npc_rating(
                log.nutrients, nutrition.micronutrients if nutrition is not None else None,
                target.calories if target is not None else None, nutrient_per_100_calories)
            if group["date"] == today:
                today_food_logs.append(log)
    (daily_progress, daily_fat_range, daily_custom_macros,
     display_protein_min, display_protein_max, display_carbs) = daily_target_progress(
        today_food_logs, daily_calorie_target, exercise_credit_today, nutrition, macro_split, preferences)
    return render_template(
        "homepage.html", values=None, error=error, meal_groups=meal_groups.values(),
        frequent_foods=frequent_foods, activity_logs=activity_logs,
        exercise_met_options=EXERCISE_METS, exercise_measurements=measurements,
        activity_baseline=activity_baseline, fixed_care_plan_target=fixed_care_plan_target,
        exercise_credit_today=exercise_credit_today, logging_day=today,
        today_saved=db.session.get(SavedEatingDay, (current_user.uid, today)) is not None,
        save_day_token=_ensure_token("_save_day_token"),
        calorie_target=target.calories if target is not None else None,
        daily_calorie_target=daily_calorie_target, daily_progress=daily_progress,
        fat_range=daily_fat_range, display_protein_min=display_protein_min,
        display_protein_max=display_protein_max, display_carbs=display_carbs,
        macro_split=macro_split, custom_macros=daily_custom_macros, nutrition_targets=nutrition,
        health_preferences=preferences,
        micronutrients_remaining=remaining_targets(today_food_logs, nutrition.micronutrients) if nutrition is not None else None,
        condition_nutrition=condition_nutrition_data(today_food_logs, daily_calorie_target),
        condition_guidance=condition_micronutrient_guidance(preferences.conditions if preferences else []),
        submission_token=submission_token, delete_token=_ensure_token("_delete_token"),
    )


def _add_activity(activity, activity_baseline, fixed_care_plan_target, measurements):
    nutrition = db.session.get(NutritionTargets, current_user.uid)
    if nutrition is None:
        raise ValueError("Complete UserInfo before logging exercise calories.")
    duration = float(request.form.get("activity_minutes", ""))
    weight = float(request.form.get("exercise_weight", ""))
    height = float(request.form.get("exercise_height", ""))
    if not all(math.isfinite(value) for value in (duration, weight, height)):
        raise ValueError("Enter exercise duration, weight, and height values.")
    if not 0 < duration <= 1440:
        raise ValueError("Exercise duration must be greater than 0 and no more than 1,440 minutes.")
    if not 10 <= weight <= 500 or not 50 <= height <= 300:
        raise ValueError("Enter a weight from 10 to 500 kg and a height from 50 to 300 cm.")
    activity_type = request.form.get("activity_type", "")
    if activity_type not in EXERCISE_METS:
        raise ValueError("Choose an exercise for the calorie estimate")
    extra_exercise = request.form.get("extra_exercise") == "1"
    if extra_exercise and activity_baseline is None:
        raise ValueError("Recalculate UserInfo to save your usual activity level before adding exercise to your target.")
    if extra_exercise and fixed_care_plan_target:
        raise ValueError("Your care-plan calorie target is fixed; log the exercise without adding it to the target.")
    burned = estimate_exercise_calories(duration, activity_type, weight, height, nutrition.age, nutrition.sex)
    db.session.add(ActivityLog(
        user_id=current_user.uid, activity=activity,
        details=ExerciseDetails(
            duration_minutes=duration, calories_burned=burned, activity_type=activity_type,
            met=EXERCISE_METS[activity_type][0], height_cm=height, weight_kg=weight,
        ),
        target_credit=ExerciseTargetCredit(
            extra=extra_exercise, active_calories=active_exercise_calories(burned, activity_type),
        ),
    ))
    if measurements is None:
        measurements = UserMeasurements(user_id=current_user.uid)
        db.session.add(measurements)
    measurements.height_cm = height
    measurements.weight_kg = weight


def _optional_positive_number(field, maximum):
    value = request.form.get(field, "").strip()
    if not value:
        return None
    amount = Decimal(value)
    if not amount.is_finite() or amount <= 0 or amount > maximum:
        raise ValueError(f"Enter a positive {field.replace('_', ' ')} no greater than {maximum}.")
    return float(amount)


def _care_plan_calories():
    calories = _optional_positive_number("custom_calories", 10000)
    if calories is not None and calories < 500:
        raise ValueError("Enter a calorie target of at least 500 kcal or leave it blank.")
    return calories


def _ensure_token(name):
    token = session.get(name)
    if token is None:
        token = secrets.token_urlsafe(32)
        session[name] = token
    return token


def _require_token(session_name, form_name):
    expected = session.get(session_name, "")
    supplied = request.form.get(form_name, "")
    if not expected or not secrets.compare_digest(supplied, expected):
        abort(400)


def _user_timezone():
    name = unquote(request.cookies.get("tracker_timezone", "UTC"))
    try:
        return ZoneInfo(name) if len(name) <= 100 else ZoneInfo("UTC")
    except (ValueError, ZoneInfoNotFoundError):
        return ZoneInfo("UTC")


def _local_day(logged_at, local_timezone):
    return _as_utc(logged_at).astimezone(local_timezone).date()


def _as_utc(value):
    return value.replace(tzinfo=value.tzinfo or timezone.utc).astimezone(timezone.utc)


def _food_logs(user_id, newest_first=False):
    query = db.session.query(FoodLog).filter_by(user_id=user_id)
    if newest_first:
        query = query.order_by(FoodLog.logged_at.desc(), FoodLog.id.desc())
    return query.all()


def _saved_days_count(user_id, first_day, last_day):
    return (db.session.query(SavedEatingDay).filter_by(user_id=user_id)
            .filter(SavedEatingDay.day >= first_day, SavedEatingDay.day <= last_day).count())


def _reopen_eating_days(user_id, days):
    for day in days:
        saved = db.session.get(SavedEatingDay, (user_id, day))
        if saved is not None:
            db.session.delete(saved)


def _validation_message(exc):
    if isinstance(exc, ValidationError):
        return exc.errors()[0]["msg"].removeprefix("Value error, ")
    return str(exc)
