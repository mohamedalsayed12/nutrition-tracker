import math
import re


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
    if "menaquinone" in name or name in ("vitamin k2", "vitamin k 2") or name.startswith("vitamin k2 "):
        return "Vitamin K2"
    if name == "vitamin k" or name.startswith("vitamin k phylloquinone"):
        return "Vitamin K"
    if name in ("choline", "choline total"):
        return "Choline"
    for nutrient in ("Calcium", "Chloride", "Chromium", "Copper", "Fluoride", "Iodine", "Iron", "Magnesium", "Manganese", "Molybdenum", "Phosphorus", "Potassium", "Selenium", "Sodium", "Zinc"):
        if name == nutrient.lower() or name.startswith(nutrient.lower() + " "):
            return nutrient
    return None


def _unit(value):
    return str(value).lower().strip().replace("Ã‚Âµ", "u").replace("ÃŽÂ¼", "u").replace("Ã¯Â¿Â½", "u")


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


def _macro_amounts_per_100g(nutrients):
    amounts = {"protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for nutrient in nutrients or ():
        name = _name(nutrient.get("name", ""))
        unit = _unit(nutrient.get("unit"))
        if unit != "g":
            continue
        try:
            amount = float(nutrient.get("per_100g"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(amount) or amount < 0:
            continue
        if name == "protein" or name.startswith("protein "):
            amounts["protein"] = max(amounts["protein"], amount)
        elif name.startswith("carbohydrate"):
            amounts["carbs"] = max(amounts["carbs"], amount)
        elif name in ("total lipid fat", "total fat", "fat") or name.startswith("total lipid"):
            amounts["fat"] = max(amounts["fat"], amount)
    return amounts


def macro_density(nutrients):
    """Macro grams per 100 kcal from per-100g nutrient rows."""
    energy = _energy_per_100g(nutrients)
    if energy is None:
        return {"energy_kcal_per_100g": None, "per_100kcal": None}
    amounts = _macro_amounts_per_100g(nutrients)
    return {
        "energy_kcal_per_100g": round(energy, 1),
        "per_100kcal": {
            name: round(nutrient_per_100_calories(amount, energy), 2)
            for name, amount in amounts.items()
        },
    }


def npc_rating(nutrients, targets, daily_calories, npc=nutrient_per_100_calories):
    if not targets or not daily_calories or daily_calories <= 0:
        return {"score": None, "reasons": ["Calculate your nutrition targets to rate this food."],
                "nutrients": [], "energy_kcal_per_100g": _energy_per_100g(nutrients)}
    energy = _energy_per_100g(nutrients)
    if energy is None:
        return {"score": None, "reasons": ["This food has no usable energy value in kcal."],
                "nutrients": [], "energy_kcal_per_100g": None}
    scored_targets = [item for item in targets if item.get("direction") != "maximum"]
    amounts = matched_micronutrients(nutrients, scored_targets, "per_100g")
    if not amounts:
        return {"score": None, "reasons": ["No matching micronutrient amounts are reported for this food."],
                "nutrients": [], "energy_kcal_per_100g": round(energy, 1)}

    contributions = []
    nutrient_rows = []
    for target in scored_targets:
        amount = amounts.get(target["name"], 0)
        target_amount = target["target"]
        if target_amount <= 0:
            continue
        per_100kcal = npc(amount, energy)
        fraction_of_target = per_100kcal / target_amount
        density_ratio = fraction_of_target * daily_calories / 100
        contribution = min(density_ratio / 2, 1)
        contributions.append((target["name"], fraction_of_target * 100, contribution))
        if target["name"] in amounts:
            nutrient_rows.append({
                "name": target["name"],
                "unit": target["unit"],
                "per_100g": round(amount, 3),
                "per_100kcal": round(per_100kcal, 3),
                "target": target_amount,
                "percent_of_target_per_100kcal": round(fraction_of_target * 100, 1),
            })

    if not contributions:
        return {"score": None, "reasons": ["No usable micronutrient targets are available."],
                "nutrients": [], "energy_kcal_per_100g": round(energy, 1)}
    score = round(100 * sum(item[2] for item in contributions) / len(contributions))
    strongest = sorted((item for item in contributions if item[0] in amounts and item[1] > 0), key=lambda item: item[2], reverse=True)[:2]
    reasons = [f"{name} provides {percent:.1f}% of your daily target per 100 kcal." for name, percent, _ in strongest]
    if not reasons:
        reasons.append("The reported micronutrients provide little of your daily targets per 100 kcal.")
    if len(amounts) < len(scored_targets):
        reasons.append(f"Only {len(amounts)} of {len(scored_targets)} target micronutrients are reported; missing data earn no points.")
    nutrient_rows.sort(key=lambda row: row["percent_of_target_per_100kcal"], reverse=True)
    return {
        "score": max(0, min(score, 100)),
        "reasons": reasons,
        "energy_kcal_per_100g": round(energy, 1),
        "nutrients": nutrient_rows,
    }


def food_nutrient_density(nutrients, targets=None, daily_calories=None):
    """Combined macro + micronutrient density for a food portion basis of 100 kcal."""
    macros = macro_density(nutrients)
    rating = npc_rating(nutrients, targets or [], daily_calories or 0)
    return {
        "score": rating["score"],
        "reasons": rating["reasons"],
        "energy_kcal_per_100g": macros["energy_kcal_per_100g"] or rating.get("energy_kcal_per_100g"),
        "macros_per_100kcal": macros["per_100kcal"],
        "micronutrients": rating["nutrients"],
    }


def remaining_targets(food_logs, targets, include_food_advice=True):
    from services.food_recommendations import attach_food_recommendations

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
        row = {"name": name, "unit": item["unit"], "target": item["target"], "limit": limit,
               "logged": logged, "remaining": round(max(item["target"] - totals[name], 0), 2) if known else None,
               "percent": percent,
               "partial": 0 < reported[name] < len(food_logs),
               "condition_adjusted": bool(item.get("condition_adjusted")),
               "custom": bool(item.get("custom"))}
        if item.get("adjusted_by"):
            row["adjusted_by"] = list(item["adjusted_by"])
        rows.append(row)
    if include_food_advice:
        return attach_food_recommendations(rows)
    return rows
