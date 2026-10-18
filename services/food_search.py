import os
import re

from flask import abort
from usda_fdc import FdcClient, FdcResourceNotFoundError


def get_food_client():
    api_key = os.getenv("FDC_API_KEY")
    if not api_key:
        raise ValueError("Food search is not configured.")
    return FdcClient(api_key)


def _matches_food_words(food, words):
    searchable = re.findall(r"[a-z0-9]+", f"{food.description} {food.brand_name or ''}".lower())
    return all(any(item.startswith(word) for item in searchable) for word in words)


def _rank_foods(foods, query):
    normalized = " ".join(query.split())
    word_count = len(re.findall(r"[a-z0-9]+", normalized))
    ranked = sorted(foods, key=lambda food: (
        food.data_type == "Branded",
        0 if food.description.lower() == normalized else
        1 if food.description.lower().startswith(normalized) else 2,
        len(re.findall(r"[a-z0-9]+", food.description.lower())) if word_count > 1 else 0,
    ))
    generic = [food for food in ranked if food.data_type != "Branded"]
    branded = [food for food in ranked if food.data_type == "Branded"]
    selected = generic[:12] + branded[:8]
    if len(selected) < 20:
        selected.extend((generic[12:] + branded[8:])[:20 - len(selected)])
    return selected


def _find_foods(client, query):
    fdc_match = re.fullmatch(r"fdc\s*[:#]?\s*(\d+)", query, re.IGNORECASE)
    if fdc_match or re.fullmatch(r"\d{2,7}", query):
        try:
            return [client.get_food(int(fdc_match.group(1) if fdc_match else query))]
        except FdcResourceNotFoundError:
            return []
    if re.fullmatch(r"\d{8,14}", query):
        results = client.search(query, page_size=100).foods
        return [food for food in results
                if (food.gtin_upc or "").lstrip("0") == query.lstrip("0")][:20]

    words = re.findall(r"[a-z0-9]+", query)
    results = client.search(query, page_size=60).foods
    matches = [food for food in results if _matches_food_words(food, words)]
    if len(words) > 1 and len(matches) < 5:
        broader = client.search(words[0], page_size=100).foods
        seen = {food.fdc_id for food in matches}
        matches.extend(food for food in broader
                       if food.fdc_id not in seen and _matches_food_words(food, words))
    return _rank_foods(matches, query)


def search_foods(query, user_id=None):
    if len(query) < 2:
        return []
    if len(query) > 80:
        abort(400, description="Search is too long.")
    if not os.getenv("FDC_API_KEY"):
        abort(503, description="Food search is not configured.")
    try:
        ordered = _find_foods(get_food_client(), query)
        return [dict(fdc_id=food.fdc_id, description=food.description,
                     data_type=food.data_type, brand_name=food.brand_name,
                     gtin_upc=getattr(food, "gtin_upc", None)) for food in ordered]
    except Exception:
        abort(502, description="Food search is temporarily unavailable.")


def search_exercises(query):
    """Backward-compatible name list; prefer search_exercise_options."""
    from services.exercise_ninjas import search_exercise_options

    return [item["name"] for item in search_exercise_options(query)]
