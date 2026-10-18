import math
import re
from datetime import timezone, timedelta

from services.nutrient_scoring import matched_micronutrients


def _name(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def food_macros(nutrients):
    chosen = {}
    for nutrient in nutrients or ():
        name = _name(nutrient.get("name", ""))
        unit = str(nutrient.get("unit", "")).lower().strip()
        key = priority = None
        if unit == "kcal" and name.startswith("energy"):
            key, priority = "Calories", 0 if name == "energy" else 1
        elif unit == "g" and name == "protein":
            key, priority = "Protein", 0
        elif unit == "g" and name in ("carbohydrate by difference", "carbohydrate by summation", "carbohydrate"):
            key, priority = "Carbohydrates", 0 if name == "carbohydrate by difference" else 1
        elif unit == "g" and name in ("total lipid fat", "fat total lipid", "total fat"):
            key, priority = "Fat", 0
        if key is None:
            continue
        try:
            amount = float(nutrient.get("eaten"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(amount) or amount < 0:
            continue
        if key not in chosen or priority < chosen[key][0]:
            chosen[key] = (priority, amount)
    return {name: value for name, (_priority, value) in chosen.items()}


def unique_week_foods(food_logs, local_timezone, week_start):
    week_end = week_start + timedelta(days=6)
    last_seen = {}
    foods = []
    for log in sorted(food_logs, key=lambda row: (row.logged_at, row.id), reverse=True):
        logged_at = log.logged_at
        if logged_at.tzinfo is None:
            logged_at = logged_at.replace(tzinfo=timezone.utc)
        day = logged_at.astimezone(local_timezone).date()
        if not week_start <= day <= week_end:
            continue
        key = (day, log.meal, log.fdc_id, log.grams)
        previous = last_seen.get(key)
        last_seen[key] = logged_at
        if previous is not None and (previous - logged_at).total_seconds() < 5:
            continue
        foods.append((day, log))
    return foods


def build_weekly_recap(food_logs, local_timezone, week_start, micronutrient_targets):
    foods = unique_week_foods(food_logs, local_timezone, week_start)
    days = {day for day, _log in foods}
    day_count = len(days)
    total_foods = len(foods)
    macro_totals = {name: 0.0 for name in ("Calories", "Protein", "Carbohydrates", "Fat")}
    macro_reported = {name: 0 for name in macro_totals}
    targets = micronutrient_targets or []
    micro_totals = {item["name"]: 0.0 for item in targets}
    micro_reported = {item["name"]: 0 for item in targets}

    for _day, log in foods:
        for name, amount in food_macros(log.nutrients).items():
            macro_totals[name] += amount
            macro_reported[name] += 1
        for name, amount in matched_micronutrients(log.nutrients, targets, "eaten").items():
            micro_totals[name] += amount
            micro_reported[name] += 1

    macros = [
        {"name": name, "unit": "kcal" if name == "Calories" else "g",
         "average": round(macro_totals[name] / day_count, 1) if day_count and macro_reported[name] else None,
         "reported": macro_reported[name], "total_foods": total_foods,
         "partial": macro_reported[name] < total_foods}
        for name in macro_totals
    ]
    micros = []
    for item in targets:
        name = item["name"]
        reported = micro_reported[name]
        average = round(micro_totals[name] / day_count, 2) if day_count and reported else None
        partial = reported < total_foods
        target = item["target"]
        if average is None:
            status = "Not reported"
        elif item.get("direction") == "maximum":
            status = "Above limit (reported)" if average > target else "Partial data" if partial else "Within limit"
        else:
            status = "Target met (reported)" if average >= target else "Partial data" if partial else "Below target"
        micros.append({"name": name, "unit": item["unit"], "average": average,
                       "target": target, "limit": item.get("direction") == "maximum",
                       "reported": reported, "total_foods": total_foods,
                       "partial": partial, "status": status})
    return {"logged_days": day_count, "food_count": total_foods, "macros": macros, "micros": micros}
