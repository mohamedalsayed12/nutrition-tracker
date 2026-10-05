import json
import os
import re
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import unquote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import PySimpleGUI as sg
import flask
import requests
from dotenv import load_dotenv
from flask import Flask, url_for, g
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user, login_required, login_user
from flask_wtf import FlaskForm
from healthsciencecalculator.get_bmr import get_bmr
from healthsciencecalculator.get_tdee import get_tdee
from sqlalchemy.exc import IntegrityError
from usda_fdc import FdcClient
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired
from extensions import db
from models import User, CalorieTarget, NutritionTargets, HealthPreferences, MealSubmission, FoodLog, ActivityLog
from nutrient_scoring import npc_rating, remaining_targets
from nutrient_targets import micronutrient_targets


load_dotenv()


#UserInfo class and what the user needs to input for their logs
class UserInfo:
    def __init__(self):
        self.activity_level = None
        self.height = None
        self.weight = None
        self.age = None
        self.gender = None


    def func(self,age,gender,height,weight,activity_level):
        self.height=height
        self.weight=weight
        self.age=age
        self.gender=gender
        self.activity_level=activity_level

##from the scientific health library it calculates the basal metabolic rate depending on age,weight,height and gender
    def calculate_bmr(self):
        return get_bmr(self.weight, self.height, self.age, self.gender)

    def calculate_tdee(self, activity_level):
        return get_tdee(self.calculate_bmr(), activity_level)




class Nutrient_Tracking_App:
    def __init__(self):
        self.nutrients = None
        self.calories = None
        self.activity = None
        self.CaloriesBurnt = None
        self.centimeters = None
        self.kilogram = None
        self.minerals = None
        self.vitamins = None
        self.male = None
        self.female=None
        self.carbohydrates = None
        self.protein = None
        self.fat = None
##def macros and identifying the three macronutrients protein,fat and carbs
    def macros(self, carbohydrates, protein, fat):
        self.carbohydrates = carbohydrates
        self.protein = protein
        self.fat = fat
##defining micros and their are two categories of micronutrients vitamins and minerals
    def micros(self, vitamins, minerals, targets):
        self.vitamins = vitamins
        self.minerals = minerals

        consumed = {**vitamins, **minerals}
        missing = []
##checking the nutrients consumed compared to the target
        for nutrient, target in targets.items():
            amount = consumed.get(nutrient, 0)
##if the amount of nutrients are less than the target then it will show you ypur missing nutrients(I want to add how to get them)
            if amount < target:
                missing.append(nutrient)
##If nothing is missing then return the phrase
        if not missing:
            return "Great job on hitting your nutrient targets!"
        else:
            return "Still missing: " + ", ".join(missing)

    def gender(self, male, female):
        self.male=male 
        self.female=female
##asking the user to input their gender
        gender = input("what is your gender")
        
        if gender == male:
            return male
        elif gender == female:
            return female

        raise ValueError('no other genders available')

##asking the user to input their weight
    def weight(self, kilogram):
        self.kilogram = kilogram

        self.kilogram = int(input("what is your weight?"))

    ##asking the user to input their height
    def height(self, centimeters):
        self.centimeters = centimeters

        self.centimeters = int(input("what is your height?"))

##creating a calculation of nutrient per calorie for each food so people know if the food they are eating is high in nutrients compared to the calories
    def npc(self, nutrient, calorie):
        if calorie <= 0:
            raise ValueError("Calories have to be greater than zero")

        return (nutrient / calorie) * 100


##Food have calories and nutrients which include macros and micros
    def food(self,calories,nutrients):
        self.calories=calories
        self.nutrients=nutrients

##The point of adding activity is so users know how many calories they have burnt in excersice to see their maintenance
    def activities(self,activity,CaloriesBurnt):
        self.activity = activity
        self.CaloriesBurnt = CaloriesBurnt

        load_dotenv()
        api_key = os.getenv("FDC_API_KEY")
        client = FdcClient(api_key)
##Loading tha API key of the FDA to breakfast lunch and dinner and having the user be able to input food
        layout_breakfast = [[sg.Input(default_text="breakfast", key="-breakfast-")]]
        layout_lunch = [[sg.Input(default_text="lunch", key="-lunch-")]]
        layout_dinner = [[sg.Input(default_text="dinner", key="-dinner-")]]
        layout_exercise = [[sg.Input(default_text="exercise", key="-activity-")]]

        layout = layout_breakfast + layout_lunch + layout_dinner + layout_exercise
        layout += [[sg.Button("Submit"), sg.Button("delete")]]

        window = sg.Window("Food and activity", layout)

        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "Quit"):
                break
            if event == "Submit":
                print(values["-breakfast-"], values["-lunch-"],
                      values["-dinner-"], values["-activity-"])


                results = client.search(values["-breakfast-"])
                print(f"Found {results.total_hits} results")
                for food in results.foods:

                    print(f"{food.description} (FDC ID: {food.fdc_id})")
                    results.total_hits
                results.foods[0].description if results.foods else None

        window.close()
        food = client.get_food(1750340)


        print(f"Food: {food.description}")
        print(f"Data Type: {food.data_type}")
        print(f"Brand: {food.brand_name}")


        print("\\nNutrients:")
        for nutrient in food.nutrients:
                print(f"{nutrient.name}: {nutrient.amount} {nutrient.unit_name}")


                foods = client.get_foods([1750340, 1750341, 1750342])


                for food in foods:
                    print(f"{food.description} ({food.data_type})")


                    foods = client.list_foods(page_size=10, page_number=1)


                    for food in foods:
                        print(f"{food.description} (FDC ID: {food.fdc_id})")


                        next_page = client.list_foods(page_size=10, page_number=2)





##Giving te user the option to search for food through using the Food's barcode
    def find_by_barcode(client, barcode):
        results = client.search(barcode, data_type=["Branded"], page_size=10)
        for food in results.foods:
            if food.gtin_upc and food.gtin_upc.lstrip("0") == barcode.lstrip("0"):
                    return client.get_food(food.fdc_id)
        return None
##implementing the login
class LoginForm(FlaskForm):
    class Meta:
        csrf = False
##creating the fields for the login
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")

app=Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"


@login_manager.user_loader
def load_user(uid):
    return db.session.get(User, int(uid))


with app.app_context():
    db.create_all()
DATABASE = os.path.join(os.path.dirname(__file__), "food_cache.sqlite3")
##getting the database for user info and logs
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()
##getting the API for foods and adding it to the database
##Search USDA foods and show the brand and source beside each suggestion.
@app.get("/api/foods")
def food_suggestions():
    query = flask.request.args.get("q", "").strip().lower()
    if len(query) < 2:
        return flask.jsonify(foods=[])
    if len(query) > 80:
        return flask.jsonify(error="Search is too long."), 400

    api_key = os.getenv("FDC_API_KEY")
    if not api_key:
        return flask.jsonify(error="Food search is not configured"), 503

    ##Cache each search for one day to avoid repeated USDA requests.
    db = get_db()
    db.execute(
        "CREATE TABLE IF NOT EXISTS food_search_cache "
        "(query TEXT PRIMARY KEY, results TEXT NOT NULL, fetched_at INTEGER NOT NULL)"
    )
    cache_key = f"{query}|foods:v3"
    cached = db.execute(
        "SELECT results FROM food_search_cache WHERE query = ? AND fetched_at > ?",
        (cache_key, int(time.time()) - 86400),
    ).fetchone()
    if cached is not None:
        return flask.jsonify(foods=json.loads(cached[0]))

    try:
        client = FdcClient(api_key)
        results = client.search(query, page_size=8)
        foods = [
            {
                "fdc_id": food.fdc_id,
                "description": food.description,
                "data_type": food.data_type,
                "brand_name": food.brand_name,
            }
            for food in results.foods
        ]
    except Exception:
        return flask.jsonify(error="Food search is temporarily unavailable."), 502

    db.execute(
        "INSERT OR REPLACE INTO food_search_cache (query, results, fetched_at) "
        "VALUES (?, ?, ?)", (cache_key, json.dumps(foods), int(time.time()))
    )
    db.commit()
    return flask.jsonify(foods=foods)


##getting the API for excersices and making it searchable in the excersices section of the tracker
@app.get("/api/exercises")
def exercise_suggestions():
    query = flask.request.args.get("q", "").strip()
    if len(query) < 2:
        return flask.jsonify(exercises=[])

    api_key = os.getenv("API_NINJAS_KEY")
    if not api_key:
        return flask.jsonify(error="Exercise search is not configured"), 503

    try:
        response = requests.get(
            "https://api.api-ninjas.com/v1/exercises",
            params={"name": query},
            headers={"X-Api-Key": api_key},
            timeout=5,
        )
        response.raise_for_status()
        exercises = [item["name"] for item in response.json()]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return flask.jsonify(error="Exercise search is temporarily unavailable."), 502

    db = get_db()
    db.execute(
        "CREATE TABLE IF NOT EXISTS exercise_search_cache "
        "(query TEXT PRIMARY KEY, results TEXT NOT NULL, fetched_at INTEGER NOT NULL)"
    )
    db.execute(
        "INSERT OR REPLACE INTO exercise_search_cache (query, results, fetched_at) "
        "VALUES (?, ?, ?)", (query, json.dumps(exercises), int(time.time()))
    )
    db.commit()
    return flask.jsonify(exercises=exercises)
##Apply pregnancy references and user-entered care-plan values to saved targets.
def configured_micronutrients(age, sex, preferences):
    pregnant = preferences is not None and "pregnancy" in (preferences.conditions or [])
    targets = micronutrient_targets(age, sex, pregnant=pregnant)
    overrides = (preferences.micronutrient_overrides or {}) if preferences is not None else {}
    for target in targets:
        if target["name"] in overrides:
            target["target"] = overrides[target["name"]]
            target["custom"] = True
    return targets


def apply_health_preferences(nutrition, preferences):
    nutrition.micronutrients = configured_micronutrients(nutrition.age, nutrition.sex, preferences)
    if preferences is None:
        return None
    calories = preferences.custom_calories
    if calories is None and "pregnancy" not in (preferences.conditions or []):
        calories = preferences.base_calories
    if preferences.custom_calories is not None:
        nutrition.protein_min = round(calories * 0.10 / 4, 1)
        nutrition.protein_max = round(calories * 0.35 / 4, 1)
    else:
        nutrition.protein_min = preferences.base_protein_min
        nutrition.protein_max = preferences.base_protein_max
    nutrition.carbs = (preferences.custom_carbs if preferences.custom_carbs is not None else
                       round(calories * 0.55 / 4, 1) if preferences.custom_calories is not None else
                       preferences.base_carbs)
    return calories


def save_calorie_target(user_id, calories):
    target = db.session.get(CalorieTarget, user_id)
    if calories is None:
        if target is not None:
            db.session.delete(target)
    elif target is None:
        db.session.add(CalorieTarget(user_id=user_id, calories=calories))
    else:
        target.calories = calories


def optional_positive_number(field, maximum):
    value = flask.request.form.get(field, "").strip()
    if not value:
        return None
    amount = Decimal(value)
    if not amount.is_finite() or amount <= 0 or amount > maximum:
        raise ValueError(f"Enter a positive {field.replace('_', ' ')} no greater than {maximum}.")
    return float(amount)


##userinfo page which has the calorie calculator and they can add their details so their maintenance can be calculated
##Calculate calorie and macro goals plus personal micronutrient targets from UserInfo.
@app.route("/UserInfo", methods=["GET", "POST"])
@login_required
def user_info_page():
    bmr = tdee = calories_for_goal = protein_min = protein_max = carbs = error = None
    micronutrients = None
    preferences = db.session.get(HealthPreferences, current_user.uid)
    pregnancy_active = preferences is not None and "pregnancy" in (preferences.conditions or [])
    if flask.request.method == "POST":
        try:
            info = UserInfo()
            info.func(
                age=int(flask.request.form["age"]),
                gender=flask.request.form["gender"],
                height=int(flask.request.form["height"]),
                weight=int(flask.request.form["weight"]),
                activity_level=flask.request.form["activity_level"],
            )
            if info.height <= 0 or info.weight <= 0:
                raise ValueError("Height and weight must be positive.")
            micronutrients = configured_micronutrients(info.age, info.gender, preferences)
            bmr = info.calculate_bmr()
            tdee = info.calculate_tdee(flask.request.form["activity_level"])
            goal = flask.request.form["goal"]
            if pregnancy_active and goal != "maintain":
                raise ValueError("Use a maintenance goal for this baseline estimate during pregnancy; set your pregnancy calorie target in Medical conditions settings.")
            ##Adjust calories for the selected weight goal before saving targets.
            if goal == "maintain":
                calories_for_goal = tdee
            elif goal == "lose_weight":
                minimum = 1200 if info.gender == "female" else 1500
                if tdee <= minimum:
                    raise ValueError("A weight-loss calorie target cannot be estimated from these inputs.")
                calories_for_goal = max(tdee - 500, minimum)
            elif goal == "gain_weight":
                calories_for_goal = tdee + 300
            else:
                raise ValueError("Choose a valid goal.")
            protein_min = round(calories_for_goal * 0.10 / 4, 1)
            protein_max = round(calories_for_goal * 0.35 / 4, 1)
            carbs = round(calories_for_goal * 0.55 / 4, 1)
            calories_for_goal = round(calories_for_goal, 1)
            ##Save the baseline and apply any condition settings and care-plan overrides.
            nutrition = db.session.get(NutritionTargets, current_user.uid)
            if nutrition is None:
                nutrition = NutritionTargets(user_id=current_user.uid)
                db.session.add(nutrition)
            nutrition.age = info.age
            nutrition.sex = info.gender
            nutrition.protein_min = protein_min
            nutrition.protein_max = protein_max
            nutrition.carbs = carbs
            nutrition.micronutrients = micronutrients
            if preferences is not None:
                preferences.base_calories = calories_for_goal
                preferences.base_carbs = carbs
                preferences.base_protein_min = protein_min
                preferences.base_protein_max = protein_max
                effective_calories = apply_health_preferences(nutrition, preferences)
                micronutrients = nutrition.micronutrients
            else:
                effective_calories = calories_for_goal
            save_calorie_target(current_user.uid, effective_calories)
            db.session.commit()
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            db.session.rollback()
            error = str(exc)
    return flask.render_template(
        "user_info.html", bmr=bmr, tdee=tdee, error=error,
        values=flask.request.form, calories_for_goal=calories_for_goal,
        protein_min=protein_min, protein_max=protein_max, carbs=carbs,
        micronutrients=micronutrients, pregnancy_active=pregnancy_active,
    )


##Let users select pregnancy, diabetes, or IBS and enter individual care-plan targets.
@app.route("/health-settings", methods=["GET", "POST"])
@login_required
def health_settings():
    nutrition = db.session.get(NutritionTargets, current_user.uid)
    if nutrition is None:
        return flask.redirect(flask.url_for("user_info_page"))
    preferences = db.session.get(HealthPreferences, current_user.uid)
    error = None
    token = flask.session.get("_health_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        flask.session["_health_token"] = token

    if flask.request.method == "POST":
        supplied = flask.request.form.get("_health_token", "")
        if not secrets.compare_digest(supplied, token):
            flask.abort(400)
        try:
            conditions = set(flask.request.form.getlist("conditions"))
            if not conditions.issubset({"pregnancy", "diabetes", "ibs"}):
                raise ValueError("Choose a listed health condition.")
            pregnant = "pregnancy" in conditions
            base_targets = micronutrient_targets(nutrition.age, nutrition.sex, pregnant=pregnant)
            trimester = None
            if pregnant:
                trimester = int(flask.request.form.get("trimester", ""))
                if trimester not in (1, 2, 3):
                    raise ValueError("Choose the pregnancy trimester.")
            custom_calories = optional_positive_number("custom_calories", 10000)
            if custom_calories is not None and custom_calories < 500:
                raise ValueError("Enter a calorie target of at least 500 kcal or leave it blank.")
            custom_carbs = optional_positive_number("custom_carbs", 1500)
            overrides = {}
            for index, target in enumerate(base_targets):
                amount = optional_positive_number(f"micro_{index}", 1000000)
                if amount is not None:
                    overrides[target["name"]] = amount

            if preferences is None:
                current_target = db.session.get(CalorieTarget, current_user.uid)
                preferences = HealthPreferences(
                    user_id=current_user.uid,
                    base_calories=current_target.calories if current_target is not None else None,
                    base_carbs=nutrition.carbs,
                    base_protein_min=nutrition.protein_min,
                    base_protein_max=nutrition.protein_max,
                )
                db.session.add(preferences)
            preferences.conditions = sorted(conditions)
            preferences.trimester = trimester
            preferences.custom_calories = custom_calories
            preferences.custom_carbs = custom_carbs
            preferences.micronutrient_overrides = overrides
            effective_calories = apply_health_preferences(nutrition, preferences)
            save_calorie_target(current_user.uid, effective_calories)
            db.session.commit()
            return flask.redirect(flask.url_for("health_settings"))
        except (ValueError, TypeError, InvalidOperation) as exc:
            db.session.rollback()
            error = str(exc)

    selected = (flask.request.form.getlist("conditions") if flask.request.method == "POST" else
                (preferences.conditions or []) if preferences is not None else [])
    pregnant = "pregnancy" in selected and 14 <= nutrition.age <= 50
    base_targets = micronutrient_targets(nutrition.age, nutrition.sex, pregnant=pregnant)
    saved_overrides = (preferences.micronutrient_overrides or {}) if preferences is not None else {}
    rows = [dict(target, index=index,
                 override=(flask.request.form.get(f"micro_{index}", "") if flask.request.method == "POST"
                           else saved_overrides.get(target["name"], "")))
            for index, target in enumerate(base_targets)]
    return flask.render_template(
        "health_settings.html", error=error, rows=rows, selected=selected,
        trimester=(flask.request.form.get("trimester", "") if flask.request.method == "POST"
                   else preferences.trimester if preferences is not None else ""),
        custom_calories=(flask.request.form.get("custom_calories", "") if flask.request.method == "POST"
                         else preferences.custom_calories if preferences is not None else ""),
        custom_carbs=(flask.request.form.get("custom_carbs", "") if flask.request.method == "POST"
                      else preferences.custom_carbs if preferences is not None else ""),
        token=token, age=nutrition.age, sex=nutrition.sex,
    )



def create_app():
    return app


##Read the browser's time zone so each user's day follows their location.
def user_timezone():
    name = unquote(flask.request.cookies.get("tracker_timezone", "UTC"))
    try:
        return ZoneInfo(name) if len(name) <= 100 else ZoneInfo("UTC")
    except (ValueError, ZoneInfoNotFoundError):
        return ZoneInfo("UTC")


##Group logs by the user's local day instead of the database's UTC timestamp.
def local_day(logged_at, local_timezone):
    if logged_at.tzinfo is None:
        logged_at = logged_at.replace(tzinfo=timezone.utc)
    return logged_at.astimezone(local_timezone).date()


##Check the session token before deleting a food or exercise entry.
def verify_delete_token():
    expected = flask.session.get("_delete_token", "")
    supplied = flask.request.form.get("_delete_token", "")
    if not expected or not secrets.compare_digest(supplied, expected):
        flask.abort(400)


##Delete the chosen food entry and any rapid duplicate copies of that entry.
@app.post("/logs/food/<int:log_id>/delete")
@login_required
def delete_food_log(log_id):
    verify_delete_token()
    local_timezone = user_timezone()
    log = db.session.get(FoodLog, log_id)
    if log is None or log.user_id != current_user.uid:
        flask.abort(404)

    matching = (
        FoodLog.query
        .filter_by(user_id=current_user.uid, meal=log.meal, fdc_id=log.fdc_id, grams=log.grams)
        .order_by(FoodLog.logged_at.desc(), FoodLog.id.desc())
        .all()
    )
    clusters = []
    previous = None
    for entry in matching:
        if (previous is None or local_day(entry.logged_at, local_timezone) != local_day(previous.logged_at, local_timezone)
                or (previous.logged_at - entry.logged_at).total_seconds() >= 5):
            clusters.append([])
        clusters[-1].append(entry)
        previous = entry
    for cluster in clusters:
        if any(entry.id == log_id for entry in cluster):
            for entry in cluster:
                db.session.delete(entry)
            break
    db.session.commit()
    return flask.redirect(flask.url_for("home_page"))


##Let a user remove only their own exercise entry.
@app.post("/logs/activity/<int:log_id>/delete")
@login_required
def delete_activity_log(log_id):
    verify_delete_token()
    log = db.session.get(ActivityLog, log_id)
    if log is None or log.user_id != current_user.uid:
        flask.abort(404)
    db.session.delete(log)
    db.session.commit()
    return flask.redirect(flask.url_for("home_page"))

@app.route("/homepage", methods=["GET", "POST"])
@login_required
def home_page():
    error = None
    local_timezone = user_timezone()
    ##Give each save a unique token so browser retries do not duplicate meals.
    submission_token = flask.request.form.get("_submission_token") or secrets.token_urlsafe(32)

    if flask.request.method == "POST":
        try:
            db.session.add(MealSubmission(user_id=current_user.uid, token=submission_token))
            api_key = os.getenv("FDC_API_KEY")
            if not api_key:
                raise ValueError("Food search is not configured.")

            client = FdcClient(api_key)
            new_food_logs = []

            for meal in ("breakfast", "lunch", "dinner"):
                selection = flask.request.form.get(meal, "").strip()
                if not selection:
                    continue

                # The suggestion contains both the name and the FDC ID.
                match = re.fullmatch(r".+ \[FDC:(\d+)\]", selection)
                if not match:
                    raise ValueError(f"Please select a {meal} food from the suggestions.")

                grams_text = flask.request.form.get(f"{meal}_grams", "").strip()
                grams = Decimal(grams_text)
                if not grams.is_finite() or grams <= 0:
                    raise ValueError(f"Enter a positive gram amount for {meal}.")

                fdc_id = int(match.group(1))
                food = client.get_food(fdc_id)

                ##Scale the USDA per-100 g values to the entered gram amount.
                nutrients = []
                for nutrient in food.nutrients:
                    if nutrient.amount is None:
                        continue  # Missing data is not the same as zero.

                    per_100g = Decimal(str(nutrient.amount))
                    eaten_amount = per_100g * grams / Decimal("100")

                    nutrients.append({
                        "name": nutrient.name,
                        "unit": nutrient.unit_name,
                        "per_100g": float(per_100g),
                        "eaten": round(float(eaten_amount), 3),
                    })

                new_food_logs.append(FoodLog(
                    user_id=current_user.uid,
                    meal=meal,
                    fdc_id=fdc_id,
                    food_name=food.description,
                    grams=float(grams),
                    nutrients=nutrients,
                ))

            for log in new_food_logs:
                db.session.add(log)

            activity = flask.request.form.get("activity", "").strip()
            if activity:
                db.session.add(ActivityLog(
                    user_id=current_user.uid,
                    activity=activity,
                ))

            db.session.commit()
            return flask.redirect(flask.url_for("home_page"))

        except IntegrityError:
            db.session.rollback()
            if db.session.get(MealSubmission, (current_user.uid, submission_token)) is not None:
                return flask.redirect(flask.url_for("home_page"))
            error = "Could not save the meal. Please try again."
        except (ValueError, InvalidOperation) as exc:
            db.session.rollback()
            error = str(exc)
        except Exception:
            db.session.rollback()
            error = "Could not retrieve or save the food details. Please try again."

    all_food_logs = (
        FoodLog.query
        .filter_by(user_id=current_user.uid)
        .order_by(FoodLog.logged_at.desc(), FoodLog.id.desc())
        .all()
    )
    ##Show one visible copy of a rapid duplicate within each meal and day.
    last_seen = {}
    meal_groups = {}
    for log in all_food_logs:
        logged_at = log.logged_at
        day = local_day(logged_at, local_timezone)
        duplicate_key = (day, log.meal, log.fdc_id, log.grams)
        previous = last_seen.get(duplicate_key)
        last_seen[duplicate_key] = logged_at
        if previous is not None and (previous - logged_at).total_seconds() < 5:
            continue
        group_key = (day, log.meal)
        if group_key not in meal_groups:
            meal_groups[group_key] = {"date": day, "meal": log.meal, "foods": []}
        meal_groups[group_key]["foods"].append(log)
    activity_logs = (
        ActivityLog.query
        .filter_by(user_id=current_user.uid)
        .order_by(ActivityLog.logged_at.desc())
        .all()
    )
    for log in activity_logs:
        log.local_date = local_day(log.logged_at, local_timezone)
    target = db.session.get(CalorieTarget, current_user.uid)
    nutrition = db.session.get(NutritionTargets, current_user.uid)
    preferences = db.session.get(HealthPreferences, current_user.uid)
    ##Refresh older saved target lists when new micronutrients are added.
    if nutrition is not None:
        current_micronutrients = configured_micronutrients(nutrition.age, nutrition.sex, preferences)
        if nutrition.micronutrients != current_micronutrients:
            nutrition.micronutrients = current_micronutrients
            db.session.commit()
    today = datetime.now(local_timezone).date()
    ##Rate each food with NPC and total today's logged micronutrients.
    today_food_logs = []
    npc_calculator = Nutrient_Tracking_App().npc
    for group in meal_groups.values():
        for log in group["foods"]:
            log.npc_result = npc_rating(
                log.nutrients,
                nutrition.micronutrients if nutrition is not None else None,
                target.calories if target is not None else None,
                npc_calculator,
            )
            if group["date"] == today:
                today_food_logs.append(log)
    micronutrients_remaining = remaining_targets(today_food_logs, nutrition.micronutrients) if nutrition is not None else None
    delete_token = flask.session.get("_delete_token")
    if delete_token is None:
        delete_token = secrets.token_urlsafe(32)
        flask.session["_delete_token"] = delete_token
##Homepage template that I got from github
    return flask.render_template(
        "homepage.html",
        values=None,
        error=error,
        meal_groups=meal_groups.values(),
        activity_logs=activity_logs,
        logging_day=today,
        calorie_target=target.calories if target is not None else None,
        nutrition_targets=nutrition,
        health_preferences=preferences,
        micronutrients_remaining=micronutrients_remaining,
        submission_token=submission_token,
        delete_token=delete_token,
    )

##Login page and login authentication
@app.route("/login", methods=["GET", "POST"])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user is None or not bcrypt.check_password_hash(user.password, form.password.data):
            return flask.render_template('login.html', form=form, erorr='Invalid email or password.')
        login_user(user)
        flask.flash('Logged in successful.')
        return flask.redirect(flask.url_for('home_page'))
    return flask.render_template('login.html', form=form)


@app.route("/register", methods=["GET", "POST"])
def registration_page():
    ##register page and authentication
    if flask.request.method == 'POST':
        name = flask.request.form.get('name', '').strip()
        email = flask.request.form.get('email', '').strip().lower()
        password = flask.request.form.get('password', '')
        if not name or not email or not password:
            return flask.render_template('register.html', error='All fields are required.'), 400
        if User.query.filter_by(email=email).first() is not None:
            return flask.render_template('register.html', error='Email is already registered.'), 409
##hashes the password to the database s it doesn't show users passwords for security reasons
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=name, email=email, password=password_hash)
        db.session.add(user)
        db.session.commit()
        return flask.redirect(flask.url_for('login_page'))

    return flask.render_template('register.html')

with app.test_request_context():
    print(url_for("home_page"))
    print(url_for("login_page"))
    print(url_for("registration_page"))
