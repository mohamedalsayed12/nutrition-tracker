import os
import re
from collections import Counter

from flask import abort
from usda_fdc import FdcClient, FdcResourceNotFoundError

from database import db
from models import FoodLog


DATA_TYPE_RANK = {
    "Foundation": 0,
    "SR Legacy": 1,
    "Survey (FNDDS)": 2,
    "Branded": 3,
}


def get_food_client():
    api_key = os.getenv("FDC_API_KEY")
    if not api_key:
        raise ValueError("Food search is not configured.")
    return FdcClient(api_key)


def _tokens(value):
    return re.findall(r"[a-z0-9]+", (value or "").lower())


def _matches_food_words(food, words):
    searchable = _tokens(f"{food.description} {food.brand_name or ''}")
    return all(any(item.startswith(word) for item in searchable) for word in words)


def _whole_word_hits(food, words):
    searchable = set(_tokens(f"{food.description} {food.brand_name or ''}"))
    return sum(1 for word in words if word in searchable)


def _relevance_score(food, query, words, personal_counts=None):
    """Lower score is better."""
    description = (food.description or "").lower().strip()
    brand = (food.brand_name or "").lower().strip()
    haystack = f"{description} {brand}".strip()
    personal_counts = personal_counts or {}

    exact = description == query
    starts = description.startswith(query)
    phrase = query in description or query in haystack
    whole_hits = _whole_word_hits(food, words)
    prefix_hits = sum(
        1 for word in words
        if any(token.startswith(word) for token in _tokens(haystack))
    )
    brand_hit = bool(brand) and any(word in brand for word in words)
    data_rank = DATA_TYPE_RANK.get(food.data_type, 4)
    # Prefer concise, specific Foundation foods over long branded ingredient lists.
    length_penalty = min(len(_tokens(description)), 20)
    personal_boost = -min(personal_counts.get(food.fdc_id, 0), 50)

    return (
        0 if exact else 1,
        0 if starts else 1,
        0 if phrase else 1,
        -whole_hits,
        -prefix_hits,
        personal_boost,  # frequently logged foods rise among accurate matches
        0 if brand_hit else 1,
        data_rank if not brand_hit else max(data_rank - 1, 0),
        length_penalty,
        description,
    )


def _rank_foods(foods, query, personal_counts=None):
    normalized = " ".join(query.split()).lower()
    words = _tokens(normalized)
    ranked = sorted(
        foods,
        key=lambda food: _relevance_score(food, normalized, words, personal_counts),
    )
    # Keep a healthy mix: prefer accurate generic matches, then branded.
    generic = [food for food in ranked if food.data_type != "Branded"]
    branded = [food for food in ranked if food.data_type == "Branded"]
    selected = generic[:12] + branded[:8]
    if len(selected) < 20:
        seen = {food.fdc_id for food in selected}
        selected.extend(
            food for food in ranked
            if food.fdc_id not in seen and len(selected) < 20
        )
    return selected[:20]


def _user_food_counts(user_id):
    if not user_id:
        return {}
    rows = (
        db.session.query(FoodLog.fdc_id, db.func.count(FoodLog.id))
        .filter(FoodLog.user_id == user_id)
        .group_by(FoodLog.fdc_id)
        .all()
    )
    return {fdc_id: count for fdc_id, count in rows}


def _serialize_food(food, personal_counts=None):
    personal_counts = personal_counts or {}
    count = personal_counts.get(food.fdc_id, 0)
    return dict(
        fdc_id=food.fdc_id,
        description=food.description,
        data_type=food.data_type,
        brand_name=food.brand_name,
        gtin_upc=getattr(food, "gtin_upc", None),
        log_count=count,
        previously_logged=count > 0,
    )


def _find_foods(client, query, personal_counts=None):
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

    words = _tokens(query)
    # Prefer accurate USDA reference foods first, then fill with branded.
    primary = client.search(
        query,
        page_size=50,
        data_type=["Foundation", "SR Legacy", "Survey (FNDDS)"],
    ).foods
    branded = client.search(query, page_size=40, data_type=["Branded"]).foods
    combined = []
    seen = set()
    for food in list(primary) + list(branded):
        if food.fdc_id in seen:
            continue
        seen.add(food.fdc_id)
        combined.append(food)

    matches = [food for food in combined if _matches_food_words(food, words)]
    if len(words) > 1 and len(matches) < 5:
        broader = client.search(words[0], page_size=80).foods
        for food in broader:
            if food.fdc_id in seen:
                continue
            if _matches_food_words(food, words):
                seen.add(food.fdc_id)
                matches.append(food)
    if not matches:
        matches = combined
    return _rank_foods(matches, query, personal_counts=personal_counts)


def search_foods(query, user_id=None):
    query = (query or "").strip()
    if len(query) < 2:
        return []
    if len(query) > 80:
        abort(400, description="Search is too long.")
    if not os.getenv("FDC_API_KEY"):
        abort(503, description="Food search is not configured.")
    personal_counts = _user_food_counts(user_id)
    try:
        ordered = _find_foods(get_food_client(), query.lower(), personal_counts)
        # Put previously logged matches first among equal relevance by re-sorting
        # with personal counts already baked into relevance.
        return [_serialize_food(food, personal_counts) for food in ordered]
    except Exception:
        abort(502, description="Food search is temporarily unavailable.")


def popular_logged_foods(user_id, meal=None, limit=12):
    """Most-logged foods for a user, optionally filtered to one meal."""
    if not user_id:
        return []
    query = db.session.query(FoodLog).filter_by(user_id=user_id)
    if meal:
        query = query.filter_by(meal=meal)
    logs = query.order_by(FoodLog.logged_at.desc()).all()
    if not logs:
        return []

    tallies = {}
    recent_duplicates = {}
    for log in logs:
        duplicate_key = (log.meal, log.fdc_id, float(log.grams))
        previous = recent_duplicates.get(duplicate_key)
        recent_duplicates[duplicate_key] = log.logged_at
        if previous is not None and 0 <= (previous - log.logged_at).total_seconds() < 5:
            continue
        entry = tallies.get(log.fdc_id)
        if entry is None:
            tallies[log.fdc_id] = {
                "fdc_id": log.fdc_id,
                "description": log.food_name,
                "grams": log.grams,
                "count": 1,
                "last_logged": log.logged_at,
                "meals": Counter({log.meal: 1}),
            }
        else:
            entry["count"] += 1
            entry["meals"][log.meal] += 1
            if log.logged_at > entry["last_logged"]:
                entry["last_logged"] = log.logged_at
                entry["grams"] = log.grams
                entry["description"] = log.food_name

    ranked = sorted(
        tallies.values(),
        key=lambda item: (item["count"], item["last_logged"]),
        reverse=True,
    )[:limit]
    for item in ranked:
        item["meals"] = [
            {"meal": name, "count": count}
            for name, count in item["meals"].most_common()
        ]
    return ranked


def search_exercises(query):
    """Backward-compatible name list; prefer search_exercise_options."""
    from services.exercise_ninjas import search_exercise_options

    return [item["name"] for item in search_exercise_options(query)]
