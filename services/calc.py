import re
from decimal import Decimal, InvalidOperation

from healthsciencecalculator.get_bmr import get_bmr
from healthsciencecalculator.get_tdee import get_tdee
from services.nutrient_targets import apply_condition_target_adjustments, micronutrient_targets
from services.weekly_recap import food_macros


class UserInfo:
    def __init__(self):
        self.activity_level = None
        self.height = None
        self.weight = None
        self.age = None
        self.gender = None

    def func(self, age, gender, height, weight, activity_level):
        self.height = height
        self.weight = weight
        self.age = age
        self.gender = gender
        self.activity_level = activity_level

    def calculate_bmr(self):
        return get_bmr(self.weight, self.height, self.age, self.gender)

    def calculate_tdee(self, activity_level):
        return get_tdee(self.calculate_bmr(), activity_level)


def calculate_goal_targets(info, goal, pregnancy_active):
    bmr = info.calculate_bmr()
    tdee = info.calculate_tdee(info.activity_level)
    if pregnancy_active and goal != "maintain":
        raise ValueError("Use a maintenance goal for this baseline estimate during pregnancy; set your pregnancy calorie target in health settings.")
    if goal == "maintain":
        calories = tdee
    elif goal == "lose_weight":
        minimum = 1200 if info.gender == "female" else 1500
        if tdee <= minimum:
            raise ValueError("A weight-loss calorie target cannot be estimated from these inputs.")
        calories = max(tdee - 500, minimum)
    elif goal == "gain_weight":
        calories = tdee + 300
    else:
        raise ValueError("Choose a valid goal.")
    return (bmr, tdee, round(calories, 1), round(calories * 0.10 / 4, 1),
            round(calories * 0.35 / 4, 1), round(calories * 0.55 / 4, 1))


def merge_condition_lists(*condition_lists):
    merged = []
    seen = set()
    for conditions in condition_lists:
        for condition in conditions or ():
            if condition not in seen:
                seen.add(condition)
                merged.append(condition)
    return merged


def configured_micronutrients(age, sex, preferences, extra_conditions=None):
    preference_conditions = (preferences.conditions or []) if preferences is not None else []
    conditions = merge_condition_lists(preference_conditions, extra_conditions)
    pregnant = "pregnancy" in conditions
    targets = micronutrient_targets(age, sex, pregnant=pregnant)
    overrides = (preferences.micronutrient_overrides or {}) if preferences is not None else {}
    for target in targets:
        if target["name"] in overrides:
            target["target"] = overrides[target["name"]]
            target["custom"] = True
    return apply_condition_target_adjustments(targets, conditions)


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
    if getattr(preferences, "custom_protein", None) is not None:
        nutrition.protein_min = preferences.custom_protein
        nutrition.protein_max = preferences.custom_protein
    nutrition.carbs = (preferences.custom_carbs if preferences.custom_carbs is not None else
                       round(calories * 0.55 / 4, 1) if preferences.custom_calories is not None else
                       preferences.base_carbs)
    return calories


def validate_care_plan_macros(calories, preferences):
    if calories is None or preferences is None:
        return
    energy = sum(value * factor for value, factor in (
        (preferences.custom_carbs or 0, 4),
        (getattr(preferences, "custom_protein", None) or 0, 4),
        (getattr(preferences, "custom_fat", None) or 0, 9),
    ))
    if energy > calories + 1:
        raise ValueError("Your carbohydrate, protein, and fat targets exceed the daily calorie target.")


def fat_target_range(calories, age):
    if calories is None or age is None:
        return None
    if age <= 3:
        minimum, maximum = 0.30, 0.40
    elif age <= 18:
        minimum, maximum = 0.25, 0.35
    else:
        minimum, maximum = 0.20, 0.35
    return round(calories * minimum / 9, 1), round(calories * maximum / 9, 1)


def custom_macro_targets(calories, split, preferences=None):
    if calories is None or split is None:
        return None
    fixed = {
        "carbs": getattr(preferences, "custom_carbs", None),
        "protein": getattr(preferences, "custom_protein", None),
        "fat": getattr(preferences, "custom_fat", None),
    }
    percentages = {
        "carbs": split.carbs_percent,
        "protein": split.protein_percent,
        "fat": split.fat_percent,
    }
    factors = {"carbs": 4, "protein": 4, "fat": 9}
    remaining_calories = calories - sum(fixed[name] * factors[name]
                                        for name in fixed if fixed[name] is not None)
    unfixed_percent = sum(percentages[name] for name in fixed if fixed[name] is None)
    result = {}
    for name in fixed:
        if fixed[name] is not None:
            result[name] = fixed[name]
        elif unfixed_percent > 0:
            result[name] = round(max(remaining_calories, 0) * percentages[name] /
                                 unfixed_percent / factors[name], 1)
        else:
            result[name] = 0.0
        result[f"{name}_overridden"] = fixed[name] is not None
    return result


EXERCISE_METS = {
    "walking": (3.8, "Walking, moderate pace"),
    "running": (9.3, "Running, about 6 mph"),
    "cycling": (7.0, "Bicycling, moderate pace"),
    "swimming": (6.0, "Swimming, leisurely"),
    "strength": (3.5, "Resistance training, varied exercises"),
    "yoga": (2.3, "Yoga, general"),
    "other_light": (2.5, "Other light activity"),
    "other_moderate": (4.0, "Other moderate activity"),
    "other_vigorous": (7.5, "Other vigorous activity"),
}


def estimate_exercise_calories(duration_minutes, activity_type, weight_kg, height_cm, age, sex):
    met = EXERCISE_METS[activity_type][0]
    if sex == "male":
        resting_kcal_day = 66.4730 + 5.0033 * height_cm + 13.7516 * weight_kg - 6.7550 * age
    elif sex == "female":
        resting_kcal_day = 655.0955 + 1.8496 * height_cm + 9.5634 * weight_kg - 4.6756 * age
    else:
        raise ValueError("Update your nutrition sex before estimating exercise calories.")
    if resting_kcal_day <= 0:
        raise ValueError("Update your nutrition measurements before estimating exercise calories.")
    return round(met * resting_kcal_day * duration_minutes / 1440, 1)


def active_exercise_calories(calories_burned, activity_type):
    met = EXERCISE_METS[activity_type][0]
    return round(calories_burned * (met - 1) / met, 1)


def scaled_food_nutrients(food, grams):
    nutrients = []
    for nutrient in food.nutrients:
        if nutrient.amount is None:
            continue
        per_100g = Decimal(str(nutrient.amount))
        eaten_amount = per_100g * grams / Decimal("100")
        nutrients.append({
            "name": nutrient.name,
            "unit": nutrient.unit_name,
            "per_100g": float(per_100g),
            "eaten": round(float(eaten_amount), 3),
        })
    return nutrients


_VOLUME_ML = {"cup": 236.5882365, "fl_oz": 29.57352956,
              "tbsp": 14.78676478, "tsp": 4.928921594, "ml": 1.0}
_VOLUME_PATTERN = re.compile(
    r"(?<!\w)(?:(\d+(?:\.\d+)?|\d+/\d+)\s+)?"
    r"(fluid\s+ounces?|fl\.?\s*oz\.?|tablespoons?|tbsp\.?|teaspoons?|tsp\.?|cups?|millilit(?:er|re)s?|ml)\b",
    re.IGNORECASE,
)


def _positive_grams(value):
    try:
        grams = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return float(grams) if grams.is_finite() and grams > 0 else None


def _portion_volume_ml(description, amount=1):
    match = _VOLUME_PATTERN.search(description or "")
    if match is None:
        return None
    quantity = match.group(1) or amount or 1
    try:
        if isinstance(quantity, str) and "/" in quantity:
            numerator, denominator = quantity.split("/", 1)
            quantity = Decimal(numerator) / Decimal(denominator)
        quantity = float(quantity)
    except (InvalidOperation, TypeError, ValueError, ZeroDivisionError):
        return None
    if not 0 < quantity < float("inf"):
        return None
    unit = match.group(2).lower().replace(".", "").replace(" ", "")
    if unit.startswith("cup"):
        key = "cup"
    elif unit.startswith(("fluid", "floz")):
        key = "fl_oz"
    elif unit.startswith(("table", "tbsp")):
        key = "tbsp"
    elif unit.startswith(("tea", "tsp")):
        key = "tsp"
    else:
        key = "ml"
    return key, quantity * _VOLUME_ML[key]


def food_measures(food):
    measures = [
        {"code": "g", "label": "grams", "grams": 1.0},
        {"code": "100g", "label": "100 grams", "grams": 100.0},
        {"code": "oz", "label": "ounces (28.35 g)", "grams": 28.349523125},
        {"code": "lb", "label": "pounds (453.59 g)", "grams": 453.59237},
        {"code": "kg", "label": "kilograms (1000 g)", "grams": 1000.0},
    ]
    volume_reference = None
    direct_volume_units = set()
    serving_size = _positive_grams(getattr(food, "serving_size", None))
    if serving_size and str(getattr(food, "serving_size_unit", None)).lower() in ("g", "gram", "grams"):
        label = getattr(food, "household_serving_fulltext", None) or "1 serving"
        measures.append({"code": "serving", "label": f"{label} ({float(serving_size):g} g)",
                         "grams": float(serving_size)})
        volume = _portion_volume_ml(label)
        if volume:
            direct_volume_units.add(volume[0])
            volume_reference = (float(serving_size), volume[1])
    for index, portion in enumerate(getattr(food, "food_portions", ())):
        portion_grams = _positive_grams(portion.gram_weight)
        if portion_grams is None:
            continue
        label = (portion.portion_description or
                 " ".join(part for part in (f"{float(portion.amount):g}" if portion.amount else "",
                                            portion.modifier, portion.measure_unit) if part).strip() or
                 "1 portion")
        if label.lower().startswith("quantity not specified"):
            continue
        measures.append({"code": f"portion:{index}",
                         "label": f"{label} ({portion_grams:g} g)",
                         "grams": portion_grams})
        volume = (_portion_volume_ml(portion.measure_unit, portion.amount)
                  or _portion_volume_ml(portion.portion_description, portion.amount))
        if volume:
            direct_volume_units.add(volume[0])
            if volume_reference is None:
                volume_reference = (portion_grams, volume[1])
    if volume_reference:
        reference_grams, reference_ml = volume_reference
        hundred_ml_grams = round(reference_grams * 100 / reference_ml, 3)
        if hundred_ml_grams > 0:
            measures.append({"code": "100ml",
                             "label": f"100 milliliters (about {hundred_ml_grams:g} g, based on USDA portion)",
                             "grams": hundred_ml_grams})
        for code, label in (("cup", "cups"), ("fl_oz", "fluid ounces"),
                            ("tbsp", "tablespoons"), ("tsp", "teaspoons"),
                            ("ml", "milliliters")):
            if code in direct_volume_units:
                continue
            grams = round(reference_grams * _VOLUME_ML[code] / reference_ml, 3)
            if grams > 0:
                measures.append({"code": f"volume:{code}",
                                 "label": f"{label} (about {grams:g} g, based on USDA portion)",
                                 "grams": grams})
    return measures


def grams_for_measure(food, quantity, measure_code):
    if not quantity.is_finite() or quantity <= 0:
        raise ValueError("Enter a positive food quantity.")
    measure = next((item for item in food_measures(food) if item["code"] == measure_code), None)
    if measure is None:
        raise ValueError("Choose an available serving size for this food.")
    grams = quantity * Decimal(str(measure["grams"]))
    if grams > 100000:
        raise ValueError("Enter a smaller food quantity.")
    return grams


def daily_target_progress(today_food_logs, daily_calorie_target, exercise_credit_today,
                          nutrition, macro_split, preferences):
    totals = {name: 0.0 for name in ("Calories", "Protein", "Carbohydrates", "Fat")}
    counts = {name: 0 for name in totals}
    for log in today_food_logs:
        for name, amount in food_macros(log.nutrients).items():
            totals[name] += amount
            counts[name] += 1
    fat_range = fat_target_range(daily_calorie_target, nutrition.age) if daily_calorie_target is not None and nutrition is not None else None
    if getattr(preferences, "custom_fat", None) is not None:
        fat_range = (preferences.custom_fat, preferences.custom_fat)
    custom_macros = custom_macro_targets(daily_calorie_target, macro_split, preferences)
    protein_min = round(daily_calorie_target * 0.10 / 4, 1) if exercise_credit_today else nutrition.protein_min if nutrition is not None else None
    protein_max = round(daily_calorie_target * 0.35 / 4, 1) if exercise_credit_today else nutrition.protein_max if nutrition is not None else None
    if getattr(preferences, "custom_protein", None) is not None:
        protein_min = protein_max = preferences.custom_protein
    carbs_target = (preferences.custom_carbs if preferences is not None and preferences.custom_carbs is not None
                    else round(daily_calorie_target * 0.55 / 4, 1) if exercise_credit_today
                    else nutrition.carbs if nutrition is not None else None)
    progress = []
    if daily_calorie_target is not None:
        progress_targets = [("Calories", daily_calorie_target, f"{daily_calorie_target} kcal")]
        if nutrition is not None:
            if custom_macros:
                progress_targets.extend((name, custom_macros[key], f"{custom_macros[key]} g")
                                        for name, key in (("Protein", "protein"), ("Carbohydrates", "carbs"), ("Fat", "fat")))
            else:
                protein_label = (f"{protein_max} g" if getattr(preferences, "custom_protein", None) is not None
                                 else f"{protein_min}Ã¢â‚¬â€œ{protein_max} g")
                progress_targets.extend((("Protein", protein_max, protein_label),
                                         ("Carbohydrates", carbs_target, f"{carbs_target} g")))
                if fat_range:
                    fat_label = (f"{fat_range[1]} g" if getattr(preferences, "custom_fat", None) is not None
                                 else f"{fat_range[0]}Ã¢â‚¬â€œ{fat_range[1]} g")
                    progress_targets.append(("Fat", fat_range[1], fat_label))
        for name, goal, target_label in progress_targets:
            reported = counts[name]
            logged = round(totals[name], 1) if reported or not today_food_logs else None
            percent = round(totals[name] / goal * 100, 1) if logged is not None and goal and goal > 0 else None
            note = ""
            if name != "Calories":
                macro_key = {"Protein": "protein", "Carbohydrates": "carbs", "Fat": "fat"}[name]
                if custom_macros and custom_macros[f"{macro_key}_overridden"]:
                    note = " (care-plan amount)"
                elif custom_macros and any(custom_macros[f"{key}_overridden"]
                                           for key in ("carbs", "protein", "fat")):
                    note = " (from remaining calories)"
                elif custom_macros:
                    note = f" ({getattr(macro_split, f'{macro_key}_percent')}%)"
                elif getattr(preferences, f"custom_{macro_key}", None) is not None:
                    note = " (care-plan amount)"
            progress.append({"name": name, "logged": logged, "target_label": target_label,
                             "unit": "kcal" if name == "Calories" else "g", "percent": percent,
                             "partial": 0 < reported < len(today_food_logs), "note": note})
    return progress, fat_range, custom_macros, protein_min, protein_max, carbs_target


def condition_nutrition_data(today_food_logs, daily_calories):
    fiber = 0.0
    reported = 0
    for log in today_food_logs:
        amount = None
        for nutrient in log.nutrients or ():
            name = re.sub(r"[^a-z0-9]+", " ", str(nutrient.get("name", "")).lower()).strip()
            if name not in ("fiber total dietary", "total dietary fiber", "dietary fiber"):
                continue
            if str(nutrient.get("unit", "")).strip().lower() != "g":
                continue
            try:
                value = Decimal(str(nutrient.get("eaten")))
            except (InvalidOperation, TypeError, ValueError):
                continue
            if value.is_finite() and value >= 0:
                amount = float(value)
                break
        if amount is not None:
            fiber += amount
            reported += 1
    goal = round(daily_calories * 14 / 1000, 1) if daily_calories is not None else None
    logged = round(fiber, 1) if reported or not today_food_logs else None
    return {
        "fiber_logged": logged,
        "fiber_goal": goal,
        "fiber_percent": round(fiber / goal * 100, 1) if logged is not None and goal else None,
        "fiber_partial": 0 < reported < len(today_food_logs),
    }


def frequent_food_choices(food_logs, per_meal=5):
    choices = {meal: {} for meal in ("breakfast", "lunch", "dinner", "snack")}
    recent_duplicates = {}
    for log in food_logs:
        if log.meal not in choices:
            continue
        duplicate_key = (log.meal, log.fdc_id, log.grams)
        previous = recent_duplicates.get(duplicate_key)
        recent_duplicates[duplicate_key] = log.logged_at
        if previous is not None and 0 <= (previous - log.logged_at).total_seconds() < 5:
            continue
        meal_choices = choices[log.meal]
        if log.fdc_id not in meal_choices:
            meal_choices[log.fdc_id] = {
                "fdc_id": log.fdc_id,
                "description": log.food_name,
                "grams": log.grams,
                "count": 0,
                "last_logged": log.logged_at,
            }
        meal_choices[log.fdc_id]["count"] += 1
    return {
        meal: sorted(items.values(),
                     key=lambda item: (item["count"], item["last_logged"]),
                     reverse=True)[:per_meal]
        for meal, items in choices.items()
    }
