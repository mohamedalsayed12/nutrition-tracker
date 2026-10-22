"""Log food from a spoken sentence (Siri via an iPhone Shortcut).

Each spoken item is matched to a food the same way the search box ranks foods,
preferring a food the user has logged before. The amount is turned into grams
with the food's own USDA serving sizes ("a medium banana" = USDA's medium
banana), and everything is logged in one go. The reply says exactly what was
logged, and what's left of today's calorie target, so Siri can read it back.
"""

import re
from datetime import datetime, timezone
from decimal import Decimal

from database import db
from models import FoodLog
from services.calc import food_measures, scaled_food_nutrients
from services.food_ranking import _match_tier, words
from services.food_search import _find_foods, _previously_logged, with_synonyms
from services.logs import invalidate_day
from services.voice_parser import parse_meal_text
from services.weekly_recap import food_macros

MASS_GRAMS = {"g": 1.0, "kg": 1000.0, "oz": 28.349523125, "lb": 453.59237}
VOLUME_ML = {"ml": 1.0, "l": 1000.0}
# Spoken unit -> words to look for in a USDA serving label.
LABEL_WORDS = {
    "cup": ("cup",), "tbsp": ("tbsp", "tablespoon"), "tsp": ("tsp", "teaspoon"),
    "slice": ("slice",), "piece": ("piece", "pc"), "bar": ("bar",), "scoop": ("scoop",),
    "can": ("can",), "bottle": ("bottle",), "fillet": ("fillet",), "bowl": ("bowl", "cup"),
    "handful": ("handful", "oz"), "serving": ("serving",),
    "small": ("small",), "medium": ("medium",), "large": ("large",), "extra large": ("extra large",),
}


# Foods people eat cooked: when Siri hears "a cup of rice" or "200 g of chicken",
# a cooked entry is chosen over raw, since raw rice has about 3x the calories
# per gram and raw meat weighs more than the cooked portion on the plate.
USUALLY_COOKED = {
    "rice", "pasta", "spaghetti", "noodle", "macaroni", "quinoa", "couscous", "oat", "porridge", "bean",
    "lentil", "chickpea", "potato", "chicken", "beef", "steak", "pork", "lamb", "turkey", "mince",
    "salmon", "cod", "tuna", "fish", "prawn", "shrimp", "bacon", "sausage",
}
COOKED_WORDS = {"cooked", "boiled", "baked", "roasted", "grilled", "broiled", "steamed", "poached", "stewed"}


def meal_for_time(local_time):
    hour = local_time.hour
    if 4 <= hour < 11:
        return "breakfast"
    if 11 <= hour < 16:
        return "lunch"
    if 16 <= hour < 22:
        return "dinner"
    return "snack"


def log_spoken_meal(user_id, text, zone, client, meal=None, now=None):
    now = now or datetime.now(timezone.utc)
    spoken_meal, items = parse_meal_text(text)
    meal = meal or spoken_meal or meal_for_time(now.astimezone(zone))
    logged, not_found = [], []
    for item in items:
        match = _match_food(user_id, client, item)
        if match is None:
            not_found.append(item.said)
            continue
        food, grams, amount_text = match
        nutrients = scaled_food_nutrients(food, Decimal(str(round(grams, 2))))
        log = FoodLog(user_id=user_id, meal=meal, fdc_id=food.fdc_id, food_name=food.description[:300],
                      grams=round(grams, 1), nutrients=nutrients, logged_at=now)
        db.session.add(log)
        invalidate_day(log)
        kcal = food_macros(nutrients).get("Calories")
        logged.append({"said": item.said, "food_name": food.description, "fdc_id": food.fdc_id,
                       "amount": amount_text, "grams": round(grams, 1),
                       "kcal": round(kcal) if kcal is not None else None})
    db.session.commit()
    return meal, logged, not_found


def _match_food(user_id, client, item):
    query = with_synonyms(item.food.lower())
    found = _find_foods(client, query, raw_first=False)
    candidates = [food for food in found if food.data_type != "Branded"][:8] or found[:8]
    query_words = words(query)
    # Only foods whose name starts with what was said: "Rice, cooked", not "Rice milk"
    # for "rice" and never "Coconut milk" for "milk".
    good = [food for food in candidates if _match_tier(food.description, query_words) <= 1]
    if not good:
        return None
    if USUALLY_COOKED & set(query_words) and not ({"raw"} & set(query_words)):
        # Stable sort: cooked entries first, otherwise keep the ranking.
        good.sort(key=lambda food: 0 if COOKED_WORDS & set(words(food.description)) else 1)
    logged_before = _previously_logged(user_id, [food.fdc_id for food in good[:5]])
    chosen = next((food for food in good[:5] if food.fdc_id in logged_before), good[0])
    try:
        food = client.get_food(chosen.fdc_id)
    except Exception:
        return None
    grams, amount_text = _grams(food, item)
    return (food, grams, amount_text) if grams and grams > 0 else None


def _grams(food, item):
    quantity = item.quantity if item.quantity is not None else 1
    if item.unit in MASS_GRAMS:
        grams = quantity * MASS_GRAMS[item.unit]
        return grams, f"{quantity:g} {item.unit}"
    measures = food_measures(food)
    portions = [m for m in measures if m["code"] not in ("g", "oz", "lb", "100g")]
    if item.unit in VOLUME_ML:
        ml = quantity * VOLUME_ML[item.unit]
        per_ml = next((m for m in measures if m["code"] == "volume:ml" or m["label"].startswith("1 ml ")), None)
        cup = _find_label(portions, ("cup",))
        if per_ml:
            return ml * per_ml["grams"], f"{ml:g} ml"
        if cup:
            return ml * cup["grams"] / 236.5882365, f"{ml:g} ml"
        return ml, f"{ml:g} ml"  # water-like density when USDA gives no volume
    if item.unit:
        measure = _find_label(portions, LABEL_WORDS.get(item.unit, (item.unit,)))
        if measure:
            return quantity * measure["grams"], f"{quantity:g} × {_plain(measure['label'])}"
    default = next((m for m in measures if m.get("default")), None)
    if default and default["code"] not in ("g", "100g"):
        return quantity * default["grams"], f"{quantity:g} × {_plain(default['label'])}"
    return quantity * 100, f"{quantity * 100:g} g (no serving size, so 100 g each)"


def _find_label(measures, label_words):
    for word in label_words:
        pattern = re.compile(rf"\b{re.escape(word)}s?\b", re.IGNORECASE)
        exact = [m for m in measures if re.match(rf"^1\s+{re.escape(word)}s?\b", m["label"], re.IGNORECASE)]
        if exact:
            return min(exact, key=lambda m: len(m["label"]))
        found = [m for m in measures if pattern.search(m["label"])]
        if found:
            return found[0]
    return None


def _plain(label):
    """"1 medium (7" to 7-7/8" long) (118 g)" -> "1 medium (118 g)"."""
    grams = re.search(r"\(([\d.]+ g)\)\s*$", label)
    name = re.sub(r"\s*\(.*\)\s*$", "", label).strip()
    return f"{name} ({grams.group(1)})" if grams else name


def spoken_reply(meal, logged, not_found, calories_left):
    if not logged and not not_found:
        return "I didn't catch any food. Try something like: two eggs and a banana for breakfast."
    parts = []
    if logged:
        foods = [item["said"] for item in logged]
        kcal = sum(item["kcal"] or 0 for item in logged)
        parts.append(f"Logged {_join(foods)} to {meal}, {kcal} calories.")
    if not_found:
        parts.append(f"I couldn't find {_join(not_found)}; add {'it' if len(not_found) == 1 else 'them'} in the app.")
    if calories_left is not None:
        parts.append(f"{abs(round(calories_left)):,} calories {'left' if calories_left >= 0 else 'over'} today.")
    return " ".join(parts)


def _join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]

