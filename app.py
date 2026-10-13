from imports import (os, re, secrets, date, datetime, timedelta, timezone,
                     Decimal, InvalidOperation, unquote, ZoneInfo, ZoneInfoNotFoundError,
                     flask, load_dotenv, Flask, current_user, login_required,
                     IntegrityError,
                     bcrypt, login_manager, configure_database, get_record, add_record,
                     delete_record, commit_changes, rollback_changes, user_food_logs,
                     user_activity_logs, saved_days_count, matching_food_logs,
                     save_calorie_target, reopen_eating_days, auth_bp, api_bp,
                     get_food_client,
                     CalorieTarget, NutritionTargets, UserMeasurements,
                     UserActivityBaseline, MacroSplit, HealthPreferences,
                     MealSubmission, FoodLog, SavedEatingDay, ActivityLog,
                     ExerciseDetails, ExerciseTargetCredit, npc_rating,
                     nutrient_per_100_calories, remaining_targets,
                     micronutrient_targets, build_weekly_recap,
                     UserInfo, calculate_goal_targets, configured_micronutrients,
                     apply_health_preferences, fat_target_range, custom_macro_targets,
                     EXERCISE_METS, estimate_exercise_calories, active_exercise_calories,
                     scaled_food_nutrients, grams_for_measure, exercise_adjusted_target,
                     daily_target_progress, weekly_target_labels,
                     frequent_food_choices, validate_care_plan_macros,
                     condition_nutrition_data, condition_micronutrient_guidance)


load_dotenv()


app=Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
configure_database(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "auth.login_page"
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)


def optional_positive_number(field, maximum):
    value = flask.request.form.get(field, "").strip()
    if not value:
        return None
    amount = Decimal(value)
    if not amount.is_finite() or amount <= 0 or amount > maximum:
        raise ValueError(f"Enter a positive {field.replace('_', ' ')} no greater than {maximum}.")
    return float(amount)


@app.route("/UserInfo", methods=["GET", "POST"])
@login_required
def user_info_page():
    bmr = tdee = calories_for_goal = protein_min = protein_max = carbs = error = None
    micronutrients = None
    preferences = get_record(HealthPreferences, current_user.uid)
    macro_split = get_record(MacroSplit, current_user.uid)
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
                raise ValueError("please enter a valid height and weight.")
            micronutrients = configured_micronutrients(info.age, info.gender, preferences)
            bmr, tdee, calories_for_goal, protein_min, protein_max, carbs = calculate_goal_targets(
                info, flask.request.form["goal"], pregnancy_active
            )
            nutrition = get_record(NutritionTargets, current_user.uid)
            if nutrition is None:
                nutrition = NutritionTargets(user_id=current_user.uid)
                add_record(nutrition)
            nutrition.age = info.age
            nutrition.sex = info.gender
            nutrition.protein_min = protein_min
            nutrition.protein_max = protein_max
            nutrition.carbs = carbs
            nutrition.micronutrients = micronutrients
            measurements = get_record(UserMeasurements, current_user.uid)
            if measurements is None:
                measurements = UserMeasurements(user_id=current_user.uid)
                add_record(measurements)
            measurements.height_cm = info.height
            measurements.weight_kg = info.weight
            activity_baseline = get_record(UserActivityBaseline, current_user.uid)
            if activity_baseline is None:
                activity_baseline = UserActivityBaseline(user_id=current_user.uid)
                add_record(activity_baseline)
            elif activity_baseline.activity_level != info.activity_level:
                activity_baseline.changed_at = datetime.now(timezone.utc)
            activity_baseline.activity_level = info.activity_level
            if preferences is not None:
                preferences.base_calories = calories_for_goal
                preferences.base_carbs = carbs
                preferences.base_protein_min = protein_min
                preferences.base_protein_max = protein_max
                effective_calories = apply_health_preferences(nutrition, preferences)
                validate_care_plan_macros(effective_calories, preferences)
                micronutrients = nutrition.micronutrients
            else:
                effective_calories = calories_for_goal
            save_calorie_target(current_user.uid, effective_calories)
            commit_changes()
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            rollback_changes()
            error = str(exc)
    return flask.render_template(
        "user_info.html", bmr=bmr, tdee=tdee, error=error,
        values=flask.request.form, calories_for_goal=calories_for_goal,
        protein_min=protein_min, protein_max=protein_max, carbs=carbs,
        fat_range=fat_target_range(calories_for_goal, info.age) if calories_for_goal is not None else None,
        macro_split=macro_split,
        custom_macros=custom_macro_targets(calories_for_goal, macro_split, preferences) if calories_for_goal is not None else None,
        micronutrients=micronutrients, pregnancy_active=pregnancy_active,
    )


@app.route("/macro-split", methods=["GET", "POST"])
@login_required
def macro_split_settings():
    nutrition = get_record(NutritionTargets, current_user.uid)
    if nutrition is None:
        return flask.redirect(flask.url_for("user_info_page"))
    split = get_record(MacroSplit, current_user.uid)
    error = None
    token = flask.session.get("_macro_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        flask.session["_macro_token"] = token
    if flask.request.method == "POST":
        if not secrets.compare_digest(flask.request.form.get("_macro_token", ""), token):
            flask.abort(400)
        try:
            action = flask.request.form.get("action", "save")
            if action == "default":
                if split is not None:
                    delete_record(split)
            elif action == "save":
                percentages = {}
                for name in ("carbs", "protein", "fat"):
                    value = Decimal(flask.request.form[f"{name}_percent"])
                    if not value.is_finite() or value < 0 or value > 100:
                        raise ValueError("Each percentage must be between 0 and 100.")
                    percentages[name] = value
                if sum(percentages.values()) != 100:
                    raise ValueError("Carbohydrates, protein, and fat must add up to 100%.")
                if split is None:
                    split = MacroSplit(user_id=current_user.uid)
                    add_record(split)
                split.carbs_percent = float(percentages["carbs"])
                split.protein_percent = float(percentages["protein"])
                split.fat_percent = float(percentages["fat"])
            else:
                raise ValueError("Choose a valid macro split action.")
            commit_changes()
            return flask.redirect(flask.url_for("home_page"))
        except (KeyError, ValueError, InvalidOperation) as exc:
            rollback_changes()
            error = str(exc) if not isinstance(exc, KeyError) else "Enter all three percentages."
    values = {
        name: flask.request.form.get(f"{name}_percent", "") if flask.request.method == "POST"
        else getattr(split, f"{name}_percent") if split is not None
        else default
        for name, default in (("carbs", 55), ("protein", 20), ("fat", 25))
    }
    preferences = get_record(HealthPreferences, current_user.uid)
    target = get_record(CalorieTarget, current_user.uid)
    return flask.render_template(
        "macro_split.html", values=values, error=error, token=token, split=split,
        calorie_target=target.calories if target is not None else None,
        overridden_macros=[name for name, field in (("carbohydrate", "custom_carbs"),
                                                  ("protein", "custom_protein"),
                                                  ("fat", "custom_fat"))
                           if preferences is not None and getattr(preferences, field) is not None],
    )


@app.route("/health-settings", methods=["GET", "POST"])
@login_required
def health_settings():
    nutrition = get_record(NutritionTargets, current_user.uid)
    if nutrition is None:
        return flask.redirect(flask.url_for("user_info_page"))
    preferences = get_record(HealthPreferences, current_user.uid)
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
            if not conditions.issubset({"pregnancy", "diabetes", "ibs", "menstruation"}):
                raise ValueError("Choose a listed medical condition.")
            if {"pregnancy", "menstruation"}.issubset(conditions):
                raise ValueError("Choose pregnancy or periods / menstruation. Bleeding during pregnancy needs clinical advice.")
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
            custom_protein = optional_positive_number("custom_protein", 1500)
            custom_fat = optional_positive_number("custom_fat", 1500)
            overrides = {}
            for index, target in enumerate(base_targets):
                amount = optional_positive_number(f"micro_{index}", 1000000)
                if amount is not None:
                    overrides[target["name"]] = amount

            if preferences is None:
                current_target = get_record(CalorieTarget, current_user.uid)
                preferences = HealthPreferences(
                    user_id=current_user.uid,
                    base_calories=current_target.calories if current_target is not None else None,
                    base_carbs=nutrition.carbs,
                    base_protein_min=nutrition.protein_min,
                    base_protein_max=nutrition.protein_max,
                )
                add_record(preferences)
            preferences.conditions = sorted(conditions)
            preferences.trimester = trimester
            preferences.custom_calories = custom_calories
            preferences.custom_carbs = custom_carbs
            preferences.custom_protein = custom_protein
            preferences.custom_fat = custom_fat
            preferences.micronutrient_overrides = overrides
            effective_calories = apply_health_preferences(nutrition, preferences)
            validate_care_plan_macros(effective_calories, preferences)
            save_calorie_target(current_user.uid, effective_calories)
            commit_changes()
            return flask.redirect(flask.url_for("health_settings"))
        except (ValueError, TypeError, InvalidOperation) as exc:
            rollback_changes()
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
        custom_protein=(flask.request.form.get("custom_protein", "") if flask.request.method == "POST"
                        else preferences.custom_protein if preferences is not None else ""),
        custom_fat=(flask.request.form.get("custom_fat", "") if flask.request.method == "POST"
                    else preferences.custom_fat if preferences is not None else ""),
        token=token, age=nutrition.age, sex=nutrition.sex,
        condition_guidance=condition_micronutrient_guidance(selected),
    )



def create_app():
    return app


def user_timezone():
    name = unquote(flask.request.cookies.get("tracker_timezone", "UTC"))
    try:
        return ZoneInfo(name) if len(name) <= 100 else ZoneInfo("UTC")
    except (ValueError, ZoneInfoNotFoundError):
        return ZoneInfo("UTC")


def local_day(logged_at, local_timezone):
    if logged_at.tzinfo is None:
        logged_at = logged_at.replace(tzinfo=timezone.utc)
    return logged_at.astimezone(local_timezone).date()


@app.get("/weekly-recap")
@login_required
def weekly_recap_page():
    local_timezone = user_timezone()
    today = datetime.now(local_timezone).date()
    current_week_start = today - timedelta(days=today.weekday())
    requested = flask.request.args.get("week", "")
    try:
        selected_day = date.fromisoformat(requested) if requested else today
    except ValueError:
        flask.abort(400)
    week_start = selected_day - timedelta(days=selected_day.weekday())
    if week_start > current_week_start:
        return flask.redirect(flask.url_for("weekly_recap_page"))
    week_end = week_start + timedelta(days=6)
    nutrition = get_record(NutritionTargets, current_user.uid)
    preferences = get_record(HealthPreferences, current_user.uid)
    split = get_record(MacroSplit, current_user.uid)
    target = get_record(CalorieTarget, current_user.uid)
    calories = target.calories if target is not None else None
    micronutrients = (configured_micronutrients(nutrition.age, nutrition.sex, preferences)
                      if nutrition is not None else [])
    food_logs = user_food_logs(current_user.uid)
    recap = build_weekly_recap(food_logs, local_timezone, week_start, micronutrients)
    saved_count = saved_days_count(current_user.uid, week_start, week_end)
    target_labels = weekly_target_labels(calories, nutrition, split, preferences)
    return flask.render_template(
        "weekly_recap.html", recap=recap, week_start=week_start, week_end=week_end,
        previous_week=(week_start - timedelta(days=7)).isoformat(),
        next_week=(week_start + timedelta(days=7)).isoformat() if week_start < current_week_start else None,
        saved_count=saved_count, target_labels=target_labels,
    )







def verify_delete_token():
    expected = flask.session.get("_delete_token", "")
    supplied = flask.request.form.get("_delete_token", "")
    if not expected or not secrets.compare_digest(supplied, expected):
        flask.abort(400)


@app.post("/days/save")
@login_required
def save_eating_day():
    expected = flask.session.get("_save_day_token", "")
    supplied = flask.request.form.get("_save_day_token", "")
    if not expected or not secrets.compare_digest(supplied, expected):
        flask.abort(400)
    try:
        day = date.fromisoformat(flask.request.form.get("day", ""))
    except ValueError:
        flask.abort(400)
    if day > datetime.now(user_timezone()).date():
        flask.abort(400)
    foods = user_food_logs(current_user.uid)
    if not any(local_day(food.logged_at, user_timezone()) == day for food in foods):
        flask.flash("Log at least one food for that day before saving it.")
        return flask.redirect(flask.url_for("home_page"))
    saved = get_record(SavedEatingDay, (current_user.uid, day))
    if saved is None:
        add_record(SavedEatingDay(user_id=current_user.uid, day=day))
        commit_changes()
    flask.flash("Day of eating saved.")
    return flask.redirect(flask.url_for("home_page"))


@app.post("/logs/food/<int:log_id>/delete")
@login_required
def delete_food_log(log_id):
    verify_delete_token()
    local_timezone = user_timezone()
    log = get_record(FoodLog, log_id)
    if log is None or log.user_id != current_user.uid:
        flask.abort(404)

    matching = matching_food_logs(current_user.uid, log.meal, log.fdc_id, log.grams)
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
            changed_days = {local_day(entry.logged_at, local_timezone) for entry in cluster}
            for entry in cluster:
                delete_record(entry)
            reopen_eating_days(current_user.uid, changed_days)
            break
    commit_changes()
    return flask.redirect(flask.url_for("home_page"))


@app.post("/logs/activity/<int:log_id>/delete")
@login_required
def delete_activity_log(log_id):
    verify_delete_token()
    log = get_record(ActivityLog, log_id)
    if log is None or log.user_id != current_user.uid:
        flask.abort(404)
    delete_record(log)
    commit_changes()
    return flask.redirect(flask.url_for("home_page"))

@app.route("/homepage", methods=["GET", "POST"])
@login_required
def home_page():
    error = None
    local_timezone = user_timezone()
    measurements = get_record(UserMeasurements, current_user.uid)
    activity_baseline = get_record(UserActivityBaseline, current_user.uid)
    preferences = get_record(HealthPreferences, current_user.uid)
    fixed_care_plan_target = preferences is not None and preferences.custom_calories is not None
    submission_token = flask.request.form.get("_submission_token") or secrets.token_urlsafe(32)

    if flask.request.method == "POST":
        try:
            add_record(MealSubmission(user_id=current_user.uid, token=submission_token))
            has_food = any(flask.request.form.get(meal, "").strip() for meal in ("breakfast", "lunch", "dinner"))
            activity = flask.request.form.get("activity", "").strip()
            if not has_food and not activity:
                raise ValueError("Choose a food or enter an exercise to save.")
            client = get_food_client() if has_food else None
            new_food_logs = []

            for meal in ("breakfast", "lunch", "dinner"):
                selection = flask.request.form.get(meal, "").strip()
                if not selection:
                    continue

                match = re.fullmatch(r".+ \[FDC:(\d+)\]", selection)
                if not match:
                    raise ValueError(f"Please select a {meal} food from the suggestions.")

                fdc_id = int(match.group(1))
                food = client.get_food(fdc_id)
                measure = flask.request.form.get(f"{meal}_measure", "").strip()
                if measure:
                    quantity = Decimal(flask.request.form.get(f"{meal}_amount", ""))
                    grams = grams_for_measure(food, quantity, measure)
                else:
                    grams = Decimal(flask.request.form.get(f"{meal}_grams", "").strip())
                    if not grams.is_finite() or grams <= 0:
                        raise ValueError(f"Enter a positive gram amount for {meal}.")

                nutrients = scaled_food_nutrients(food, grams)

                new_food_logs.append(FoodLog(
                    user_id=current_user.uid,
                    meal=meal,
                    fdc_id=fdc_id,
                    food_name=food.description,
                    grams=float(grams),
                    nutrients=nutrients,
                    logged_at=datetime.now(timezone.utc),
                ))

            for log in new_food_logs:
                add_record(log)
            if new_food_logs:
                reopen_eating_days(current_user.uid, {
                    local_day(log.logged_at, local_timezone) for log in new_food_logs
                })

            if activity:
                nutrition_for_exercise = get_record(NutritionTargets, current_user.uid)
                if nutrition_for_exercise is None:
                    raise ValueError("Complete UserInfo before logging exercise calories.")
                duration = int(flask.request.form.get("activity_minutes", ""))
                weight = int(flask.request.form.get("exercise_weight", ""))
                height = int(flask.request.form.get("exercise_height", ""))
                if not all(value.is_finite() for value in (duration, weight, height)):
                    raise ValueError("Enter exercise duration, weight, and height values.")
                if not 0 < duration <= 1440:
                    raise ValueError("Exercise duration must be greater than 0 and no more than 1,440 minutes.")
                if not 10 <= weight <= 500 or not 50 <= height <= 300:
                    raise ValueError("Enter a weight from 10 to 500 kg and a height from 50 to 300 cm.")
                activity_type = flask.request.form.get("activity_type", "")
                if activity_type not in EXERCISE_METS:
                    raise ValueError("Choose an exercise for the calorie estimate")
                calories_burned = estimate_exercise_calories(
                    float(duration), activity_type, float(weight), float(height),
                    nutrition_for_exercise.age, nutrition_for_exercise.sex,
                )
                extra_exercise = flask.request.form.get("extra_exercise") == "1"
                if extra_exercise and activity_baseline is None:
                    raise ValueError("Recalculate UserInfo to save your usual activity level before adding exercise to your target.")
                if extra_exercise and fixed_care_plan_target:
                    raise ValueError("Your care-plan calorie target is fixed; log the exercise without adding it to the target.")
                met = EXERCISE_METS[activity_type][0]
                active_calories = active_exercise_calories(calories_burned, activity_type)
                add_record(ActivityLog(
                    user_id=current_user.uid,
                    activity=activity,
                    details=ExerciseDetails(
                        duration_minutes=float(duration), calories_burned=calories_burned,
                        activity_type=activity_type, met=met,
                        height_cm=float(height), weight_kg=float(weight),
                    ),
                    target_credit=ExerciseTargetCredit(
                        extra=extra_exercise, active_calories=active_calories,
                    ),
                ))
                if measurements is None:
                    measurements = UserMeasurements(user_id=current_user.uid)
                    add_record(measurements)
                measurements.height_cm = float(height)
                measurements.weight_kg = float(weight)

            commit_changes()
            return flask.redirect(flask.url_for("home_page"))

        except IntegrityError:
            rollback_changes()
            if get_record(MealSubmission, (current_user.uid, submission_token)) is not None:
                return flask.redirect(flask.url_for("home_page"))
            error = "Could not save the meal. Please try again."
        except (ValueError, InvalidOperation) as exc:
            rollback_changes()
            error = str(exc)
        except Exception:
            rollback_changes()
            error = "Could not retrieve or save the food details. Please try again."

    all_food_logs = user_food_logs(current_user.uid, newest_first=True)
    frequent_foods = frequent_food_choices(all_food_logs)
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
    activity_logs = user_activity_logs(current_user.uid)
    for log in activity_logs:
        log.local_date = local_day(log.logged_at, local_timezone)
    target = get_record(CalorieTarget, current_user.uid)
    nutrition = get_record(NutritionTargets, current_user.uid)
    macro_split = get_record(MacroSplit, current_user.uid)
    if nutrition is not None:
        current_micronutrients = configured_micronutrients(nutrition.age, nutrition.sex, preferences)
        if nutrition.micronutrients != current_micronutrients:
            nutrition.micronutrients = current_micronutrients
            commit_changes()
    today = datetime.now(local_timezone).date()
    today_saved = get_record(SavedEatingDay, (current_user.uid, today)) is not None
    save_day_token = flask.session.get("_save_day_token")
    if save_day_token is None:
        save_day_token = secrets.token_urlsafe(32)
        flask.session["_save_day_token"] = save_day_token

    exercise_credit_today, daily_calorie_target = exercise_adjusted_target(
        target, activity_logs, today, activity_baseline, fixed_care_plan_target
    )
    today_food_logs = []
    npc_calculator = nutrient_per_100_calories
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
    (daily_progress, daily_fat_range, daily_custom_macros,
     protein_min, protein_max, carbs_target) = daily_target_progress(
        today_food_logs, daily_calorie_target, exercise_credit_today,
        nutrition, macro_split, preferences,
    )
    condition_nutrition = condition_nutrition_data(today_food_logs, daily_calorie_target)
    delete_token = flask.session.get("_delete_token")
    if delete_token is None:
        delete_token = secrets.token_urlsafe(32)
        flask.session["_delete_token"] = delete_token
    return flask.render_template(
        "homepage.html",
        values=None,
        error=error,
        meal_groups=meal_groups.values(),
        frequent_foods=frequent_foods,
        activity_logs=activity_logs,
        exercise_met_options=EXERCISE_METS,
        exercise_measurements=measurements,
        activity_baseline=activity_baseline,
        fixed_care_plan_target=fixed_care_plan_target,
        exercise_credit_today=exercise_credit_today,
        logging_day=today,
        today_saved=today_saved,
        save_day_token=save_day_token,
        calorie_target=target.calories if target is not None else None,
        daily_calorie_target=daily_calorie_target,
        daily_progress=daily_progress,
        fat_range=daily_fat_range,
        display_protein_min=protein_min,
        display_protein_max=protein_max,
        display_carbs=carbs_target,
        macro_split=macro_split,
        custom_macros=daily_custom_macros,
        nutrition_targets=nutrition,
        health_preferences=preferences,
        micronutrients_remaining=micronutrients_remaining,
        condition_nutrition=condition_nutrition,
        condition_guidance=condition_micronutrient_guidance(preferences.conditions if preferences else []),
        submission_token=submission_token,
        delete_token=delete_token,
    )
