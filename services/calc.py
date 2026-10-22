import re
from datetime import timezone
from decimal import Decimal, InvalidOperation

from services.nutrient_targets import apply_menstruation_targets, micronutrient_targets
from services.weekly_recap import food_macros


# Activity multipliers for total daily energy expenditure (TDEE = BMR x factor).
ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "lightly active": 1.375,
    "moderately active": 1.55,
    "very active": 1.725,
    "extra active": 1.9,
}


def mifflin_st_jeor_bmr(weight_kg, height_cm, age, sex):
    """Resting energy in kcal/day from weight, height, age and sex.

    Mifflin-St Jeor (1990) is the equation the Academy of Nutrition and Dietetics
    recommends for healthy adults, and the one Cronometer uses by default. It is
    closer to measured values than the older Harris-Benedict equation.
    https://pubmed.ncbi.nlm.nih.gov/2305711/
    """
    if weight_kg <= 0 or height_cm <= 0 or age <= 0:
        raise ValueError("Weight, height and age must be positive.")
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if sex == "male":
        return round(base + 5, 1)
    if sex == "female":
        return round(base - 161, 1)
    raise ValueError('Sex must be "male" or "female".')


# Protein per kg of body weight for the minimum target.
# - 0.8 g/kg: the adult RDA (National Academies, Dietary Reference Intakes).
# - 0.85 g/kg at age 18: the RDA for ages 14-18.
# - 1.0 g/kg from age 65: PROT-AGE and ESPEN advice for older adults, to limit muscle loss.
# - 1.2 g/kg when losing weight: helps keep muscle in a calorie deficit.
# - 1.6 g/kg when gaining weight: where extra protein stops adding muscle in
#   resistance training (Morton et al., 2018 meta-analysis).
PROTEIN_GOAL_MINIMUM_PER_KG = {"maintain": 0.0, "lose_weight": 1.2, "gain_weight": 1.6}


def protein_per_kg(age, goal="maintain"):
    rda = 0.85 if age <= 18 else 1.0 if age >= 65 else 0.8
    return max(rda, PROTEIN_GOAL_MINIMUM_PER_KG.get(goal, 0.0))


def protein_targets(calories, weight_kg, age, goal="maintain"):
    """(minimum, maximum) grams of protein a day.

    The minimum scales with body weight, age and goal; the maximum is 35% of
    calories, the top of the acceptable range, and never below the minimum.
    """
    minimum = round(weight_kg * protein_per_kg(age, goal), 1)
    return minimum, protein_maximum(calories, minimum)


def protein_maximum(calories, minimum):
    return max(round(calories * 0.35 / 4, 1), minimum or 0)


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
        return mifflin_st_jeor_bmr(self.weight, self.height, self.age, self.gender)

    def calculate_tdee(self, activity_level):
        if activity_level not in ACTIVITY_FACTORS:
            raise ValueError("Choose a valid activity level.")
        return round(self.calculate_bmr() * ACTIVITY_FACTORS[activity_level], 1)


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
    protein_min, protein_max = protein_targets(calories, info.weight, info.age, goal)
    return (bmr, tdee, round(calories, 1), protein_min, protein_max, round(calories * 0.55 / 4, 1))


def configured_micronutrients(age, sex, preferences):
    pregnant = preferences is not None and "pregnancy" in (preferences.conditions or [])
    targets = micronutrient_targets(age, sex, pregnant=pregnant)
    if preferences is not None and "menstruation" in (preferences.conditions or []):
        apply_menstruation_targets(targets, age)
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
        # The weight-based minimum stays; only the 35%-of-calories maximum follows the care plan.
        nutrition.protein_min = (preferences.base_protein_min if preferences.base_protein_min is not None
                                 else round(calories * 0.10 / 4, 1))
        nutrition.protein_max = protein_maximum(calories, nutrition.protein_min)
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
    if sex not in ("male", "female"):
        raise ValueError("Update your nutrition sex before estimating exercise calories.")
    try:
        resting_kcal_day = mifflin_st_jeor_bmr(weight_kg, height_cm, age, sex)
    except ValueError:
        resting_kcal_day = 0
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


# Portion words that describe a cut or prepared shape. A volume measured this way
# ("1 cup, sliced") cannot be turned into tablespoons or millilitres sensibly.
_CUT_WORDS = re.compile(r"slice|chop|dice|cube|piece|half|halves|quarter|shred|grate|mash|"
                        r"floret|strip|wedge|ring|spear|stalk|packed|crumble|whole", re.IGNORECASE)
_PLACEHOLDER_UNITS = {"undetermined", "unit", "units", ""}


# FNDDS lists reference amounts that are not servings anyone eats, such as
# "Guideline amount per fl oz of beverage" (2.5 g for milk). They are skipped.
_SKIPPED_PORTIONS = ("quantity not specified", "guideline amount")
# USDA jargon for a standard serving: Reference Amount Customarily Consumed, and
# the Nutrition Labeling and Education Act serving.
_SERVING_JARGON = re.compile(r"^\s*1\s+(?:RACC|NLEA serving)\s*$", re.IGNORECASE)
# Portions that are a package size rather than a normal helping, so they are not pre-selected.
_NOT_A_DEFAULT = re.compile(r"\b(?:container|package|school|can|bunch|jar|bottle|loaf)\b", re.IGNORECASE)


def _portion_label(portion):
    label = _raw_portion_label(portion)
    return "1 serving" if _SERVING_JARGON.match(label or "") else label


def _raw_portion_label(portion):
    if portion.portion_description and not portion.portion_description.lower().startswith(_SKIPPED_PORTIONS):
        return portion.portion_description
    unit = (portion.measure_unit or "").strip()
    if unit.lower() in _PLACEHOLDER_UNITS:
        unit = ""
    amount = f"{float(portion.amount):g}" if portion.amount else "1"
    return " ".join(part for part in (amount, (portion.modifier or "").strip(), unit) if part).strip()


def food_measures(food):
    """Serving sizes for a food, ordered like Cronometer: household portions first.

    Exactly one measure has "default": True, the one to pre-select: a "medium"
    portion if USDA has one, else the first portion that is a normal helping
    rather than a package size, else the first portion, else 100 g.
    """
    portions = []
    volume_reference = None
    direct_volume_units = set()
    serving_size = _positive_grams(getattr(food, "serving_size", None))
    if serving_size and str(getattr(food, "serving_size_unit", None)).lower() in ("g", "gram", "grams"):
        label = getattr(food, "household_serving_fulltext", None) or "1 serving"
        portions.append({"code": "serving", "label": f"{label} ({float(serving_size):g} g)",
                         "grams": float(serving_size)})
        volume = _portion_volume_ml(label)
        if volume and not _CUT_WORDS.search(label):
            direct_volume_units.add(volume[0])
            volume_reference = (float(serving_size), volume[1])
    for index, portion in enumerate(getattr(food, "food_portions", ()) or ()):
        portion_grams = _positive_grams(portion.gram_weight)
        if portion_grams is None:
            continue
        if (portion.portion_description or "").lower().startswith(_SKIPPED_PORTIONS):
            continue
        label = _portion_label(portion) or "1 portion"
        portions.append({"code": f"portion:{index}",
                         "label": f"{label} ({portion_grams:g} g)",
                         "grams": portion_grams})
        if _CUT_WORDS.search(label):
            continue
        volume = (_portion_volume_ml(portion.measure_unit, portion.amount)
                  or _portion_volume_ml(portion.portion_description, portion.amount))
        if volume:
            direct_volume_units.add(volume[0])
            if volume_reference is None:
                volume_reference = (portion_grams, volume[1])

    volumes = []
    if volume_reference:
        reference_grams, reference_ml = volume_reference
        for code, label in (("cup", "1 cup"), ("tbsp", "1 tbsp"), ("tsp", "1 tsp"),
                            ("fl_oz", "1 fl oz"), ("ml", "1 ml")):
            if code in direct_volume_units:
                continue
            grams = round(reference_grams * _VOLUME_ML[code] / reference_ml, 3)
            if grams > 0:
                volumes.append({"code": f"volume:{code}", "label": f"{label} ({grams:g} g)", "grams": grams})

    measures = portions + volumes + [
        {"code": "g", "label": "g", "grams": 1.0},
        {"code": "oz", "label": "oz (28.35 g)", "grams": 28.349523125},
        {"code": "lb", "label": "lb (453.59 g)", "grams": 453.59237},
        {"code": "100g", "label": "100 g", "grams": 100.0},
    ]
    default = (next((item for item in portions if re.search(r"\bmedium\b", item["label"], re.IGNORECASE)), None)
               or next((item for item in portions if not _NOT_A_DEFAULT.search(item["label"])), None)
               or (portions[0] if portions else None)
               or next(item for item in measures if item["code"] == "100g"))
    for item in measures:
        item["default"] = item is default
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
    # Extra exercise raises the calorie target, so the 35% maximum rises with it; the
    # weight-based minimum does not change.
    protein_min = nutrition.protein_min if nutrition is not None else None
    protein_max = (protein_maximum(daily_calorie_target, protein_min) if exercise_credit_today and nutrition is not None
                   else nutrition.protein_max if nutrition is not None else None)
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
                                 else f"{protein_min}–{protein_max} g")
                progress_targets.extend((("Protein", protein_max, protein_label),
                                         ("Carbohydrates", carbs_target, f"{carbs_target} g")))
                if fat_range:
                    fat_label = (f"{fat_range[1]} g" if getattr(preferences, "custom_fat", None) is not None
                                 else f"{fat_range[0]}–{fat_range[1]} g")
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
                             "bar_width": min(percent, 100) if percent is not None else 0,
                             "partial": 0 < reported < len(today_food_logs), "note": note})
    return progress, fat_range, custom_macros, protein_min, protein_max, carbs_target


def _as_utc(value):
    return value.replace(tzinfo=value.tzinfo or timezone.utc).astimezone(timezone.utc)


def exercise_adjusted_target(target, activity_logs, today, activity_baseline, fixed_care_plan_target):
    credit = 0
    if target is not None and activity_baseline is not None and not fixed_care_plan_target:
        changed_at = _as_utc(activity_baseline.changed_at)
        credit = round(sum(
            log.target_credit.active_calories for log in activity_logs
            if getattr(log, "local_date", None) == today and log.target_credit is not None
            and log.target_credit.extra and _as_utc(log.logged_at) >= changed_at
        ), 1)
    calories = round(target.calories + credit, 1) if target is not None else None
    return credit, calories


def weekly_target_labels(calories, nutrition, split, preferences):
    custom = custom_macro_targets(calories, split, preferences)
    fat_range = fat_target_range(calories, nutrition.age) if calories is not None and nutrition is not None else None
    protein_override = getattr(preferences, "custom_protein", None)
    fat_override = getattr(preferences, "custom_fat", None)
    return {
        "Calories": f"{calories} kcal" if calories is not None else "Not set",
        "Protein": (f"{custom['protein']} g" if custom else
                    f"{protein_override} g" if protein_override is not None else
                    f"{nutrition.protein_min}–{nutrition.protein_max} g" if nutrition else "Not set"),
        "Carbohydrates": (f"{custom['carbs']} g" if custom else
                          f"{nutrition.carbs} g" if nutrition else "Not set"),
        "Fat": (f"{custom['fat']} g" if custom else
                f"{fat_override} g" if fat_override is not None else
                f"{fat_range[0]}–{fat_range[1]} g" if fat_range else "Not set"),
    }


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
