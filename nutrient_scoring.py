
from imports import math, re


def _name(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def nutrient_per_100_calories(nutrient, calorie):
    if calorie <= 0:
        raise ValueError("Calories have to be greater than zero")
    return nutrient / calorie * 100


def _target_name(value):
    name = _name(value)
    if name.startswith("vitamin a ") and ("rae" in name or "retinol activity equivalent" in name):
        return "Vitamin A"
    if name == "vitamin c" or name.startswith("vitamin c total ascorbic acid"):
        return "Vitamin C"
    if name == "vitamin d" or name.startswith("vitamin d d2 d3"):
        return "Vitamin D"
    if name == "vitamin b12" or name.startswith("vitamin b 12"):
        return "Vitamin B12"
    if name == "thiamin" or name.startswith("thiamin ") or name.startswith("vitamin b 1"):
        return "Thiamin (B1)"
    if name == "riboflavin" or name.startswith("riboflavin ") or name.startswith("vitamin b 2"):
        return "Riboflavin (B2)"
    if name == "niacin" or name.startswith("niacin ") or name.startswith("vitamin b 3"):
        return "Niacin (B3)"
    if name.startswith("pantothenic acid") or name.startswith("vitamin b 5"):
        return "Pantothenic acid (B5)"
    if name == "vitamin b6" or name.startswith("vitamin b 6"):
        return "Vitamin B6"
    if name == "biotin" or name.startswith("biotin ") or name.startswith("vitamin b 7"):
        return "Biotin (B7)"
    if name.startswith("folate dfe") or name.startswith("folate dietary folate equivalents"):
        return "Folate (B9)"
    if name == "vitamin e" or name.startswith("vitamin e alpha tocopherol"):
        return "Vitamin E"
    if name == "vitamin k" or name.startswith("vitamin k phylloquinone"):
        return "Vitamin K"
    if name in ("choline", "choline total"):
        return "Choline"
    for nutrient in ("Calcium", "Chloride", "Chromium", "Copper", "Fluoride", "Iodine", "Iron", "Magnesium", "Manganese", "Molybdenum", "Phosphorus", "Potassium", "Selenium", "Sodium", "Zinc"):
        if name == nutrient.lower() or name.startswith(nutrient.lower() + " "):
            return nutrient
    return None


def _unit(value):
    return str(value).lower().strip().replace("µ", "u").replace("μ", "u").replace("�", "u")


def _convert(amount, source_unit, target_unit):
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(amount) or amount < 0:
        return None

    source = _unit(source_unit)
    target = "mcg" if target_unit.startswith("mcg") else "mg" if target_unit.startswith("mg") else target_unit
    factor_to_mg = {"g": 1000, "mg": 1, "ug": 0.001, "mcg": 0.001}
    if source not in factor_to_mg or target not in ("mg", "mcg"):
        return None
    milligrams = amount * factor_to_mg[source]
    return milligrams if target == "mg" else milligrams * 1000


def matched_micronutrients(nutrients, targets, amount_field):
    target_by_name = {item["name"]: item for item in targets}
    matched = {}
    for nutrient in nutrients or ():
        name = _target_name(nutrient.get("name", ""))
        if name not in target_by_name:
            continue
        amount = _convert(nutrient.get(amount_field), nutrient.get("unit"), target_by_name[name]["unit"])
        if amount is not None:
            matched[name] = max(amount, matched.get(name, 0))
    return matched


def _energy_per_100g(nutrients):
    candidates = []
    for nutrient in nutrients or ():
        name = _name(nutrient.get("name", ""))
        if not name.startswith("energy") or _unit(nutrient.get("unit")) != "kcal":
            continue
        try:
            amount = float(nutrient.get("per_100g"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(amount) and amount > 0:
            candidates.append((name != "energy", amount))
    return min(candidates)[1] if candidates else None


def npc_rating(nutrients, targets, daily_calories, npc):
    if not targets or not daily_calories or daily_calories <= 0:
        return {"score": None, "reasons": ["Calculate your UserInfo targets to rate this food."]}
    energy = _energy_per_100g(nutrients)
    if energy is None:
        return {"score": None, "reasons": ["This food has no usable energy value in kcal."]}
    scored_targets = [item for item in targets if item.get("direction") != "maximum"]
    amounts = matched_micronutrients(nutrients, scored_targets, "per_100g")
    if not amounts:
        return {"score": None, "reasons": ["No matching micronutrient amounts are reported for this food."]}

    contributions = []
    for target in scored_targets:
        amount = amounts.get(target["name"], 0)
        target_amount = target["target"]
        if target_amount <= 0:
            continue
        per_100kcal = npc(amount, energy)
        fraction_of_target = per_100kcal / target_amount
        density_ratio = fraction_of_target * daily_calories / 100
        contributions.append((target["name"], fraction_of_target * 100, min(density_ratio / 2, 1)))

    if not contributions:
        return {"score": None, "reasons": ["No usable micronutrient targets are available."]}
    score = round(100 * sum(item[2] for item in contributions) / len(contributions))
    strongest = sorted((item for item in contributions if item[0] in amounts and item[1] > 0), key=lambda item: item[2], reverse=True)[:2]
    reasons = [f"{name} provides {percent:.1f}% of your daily target per 100 kcal." for name, percent, _ in strongest]
    if not reasons:
        reasons.append("The reported micronutrients provide little of your daily targets per 100 kcal.")
    if len(amounts) < len(scored_targets):
        reasons.append(f"Only {len(amounts)} of {len(scored_targets)} target micronutrients are reported; missing data earn no points.")
    return {"score": max(0, min(score, 100)), "reasons": reasons}


def remaining_targets(food_logs, targets):
    totals = {item["name"]: 0.0 for item in targets}
    reported = {item["name"]: 0 for item in targets}
    for log in food_logs:
        for name, amount in matched_micronutrients(log.nutrients, targets, "eaten").items():
            totals[name] += amount
            reported[name] += 1
    rows = []
    for item in targets:
        name = item["name"]
        known = reported[name] > 0 or not food_logs
        logged = round(totals[name], 2) if known else None
        limit = item.get("direction") == "maximum"
        percent = round(totals[name] / item["target"] * 100, 1) if known and item["target"] > 0 else None
        rows.append({"name": name, "unit": item["unit"], "target": item["target"], "limit": limit,
                     "logged": logged, "remaining": round(max(item["target"] - totals[name], 0), 2) if known else None,
                     "percent": percent, "bar_width": min(percent, 100) if percent is not None else 0,
                     "partial": 0 < reported[name] < len(food_logs)})
    return rows
