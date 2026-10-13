
from imports import os, re, flask, requests, Blueprint, FdcClient, current_user
from usda_fdc import FdcResourceNotFoundError
from db import (cached_food_search, save_food_search, save_exercise_search,
                indexed_food_search, user_food_search_counts)
from calc import food_measures


api_bp = Blueprint("api", __name__)


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


def _rank_indexed_foods(foods, query):
    counts = user_food_search_counts(current_user.uid) if current_user.is_authenticated else {}
    normalized = " ".join(query.split())
    words = re.findall(r"\w+", normalized, re.UNICODE)
    first_word = words[0]
    def sequence_at(tokens, expected):
        return next((index for index in range(len(tokens) - len(expected) + 1)
                     if tokens[index:index + len(expected)] == expected), None)

    def rank(food):
        description = food["description"].lower()
        brand = (food["brand_name"] or "").lower()
        description_words = re.findall(r"\w+", description, re.UNICODE)
        combined_words = re.findall(r"\w+", brand, re.UNICODE) + description_words
        description_position = sequence_at(description_words, words)
        combined_position = sequence_at(combined_words, words)
        description_prefixes = all(
            any(token.startswith(word) for token in description_words) for word in words)
        match_quality = (
            0 if description_words == words else
            1 if description_position is not None else
            2 if description_prefixes else
            3 if combined_position is not None else
            4 if all(word in combined_words for word in words) else 5
        )
        return (
            -counts.get(food["fdc_id"], 0),
            match_quality,
            description_position if description_position is not None else 999,
            0 if match_quality >= 3 and brand.startswith(first_word) else 1,
            len(description_words),
            len(description),
            0 if food["data_type"] == "Foundation" else
            1 if food["data_type"] == "SR Legacy" else
            2 if food["data_type"] != "Branded" else 3,
        )
    dated = sorted(foods, key=lambda food: food["publication_date"] or "", reverse=True)
    ranked = sorted(dated, key=rank)
    distinct = []
    seen = set()
    for food in ranked:
        identity = (food["description"].strip().casefold(),
                    (food["brand_name"] or "").strip().casefold())
        if identity not in seen:
            distinct.append(food)
            seen.add(identity)
    generic = [food for food in distinct if food["data_type"] != "Branded"]
    branded = [food for food in distinct if food["data_type"] == "Branded"]
    selected = generic[:12] + branded[:8]
    if len(selected) < 20:
        selected.extend((generic[12:] + branded[8:])[:20 - len(selected)])
    return selected


def _find_indexed_foods(query):
    fdc_match = re.fullmatch(r"fdc\s*[:#]?\s*(\d+)", query, re.IGNORECASE)
    fdc_id = int(fdc_match.group(1)) if fdc_match else (
        int(query) if re.fullmatch(r"\d{2,7}", query) else None)
    barcode = query if re.fullmatch(r"\d{8,14}", query) else None
    words = re.findall(r"\w+", query, re.UNICODE)
    foods = indexed_food_search(words, fdc_id=fdc_id, barcode=barcode)
    if foods is None:
        return None
    if fdc_id is not None or not words:
        selected = foods[:20]
    else:
        selected = _rank_indexed_foods(foods, query)
    return [{key: food[key] for key in
             ("fdc_id", "description", "data_type", "brand_name", "gtin_upc")}
            for food in selected]


@api_bp.get("/api/foods")
def food_suggestions():
    query = flask.request.args.get("q", "").strip().lower()
    if len(query) < 2:
        return flask.jsonify(foods=[])
    if len(query) > 80:
        return flask.jsonify(error="Search is too long."), 400

    try:
        indexed = _find_indexed_foods(query)
        if indexed is not None:
            return flask.jsonify(foods=indexed)
    except Exception:
        return flask.jsonify(error="Food search index is temporarily unavailable."), 502

    if not os.getenv("FDC_API_KEY"):
        return flask.jsonify(error="Food search is not configured"), 503

    cache_key = f"{query}|search:v8"
    cached = cached_food_search(cache_key)
    if cached is not None:
        return flask.jsonify(foods=cached)

    try:
        client = get_food_client()
        ordered = _find_foods(client, query)
        foods = [
            {
                "fdc_id": food.fdc_id,
                "description": food.description,
                "data_type": food.data_type,
                "brand_name": food.brand_name,
                "gtin_upc": getattr(food, "gtin_upc", None),
            }
            for food in ordered
        ]
    except Exception:
        return flask.jsonify(error="Food search is temporarily unavailable."), 502

    save_food_search(cache_key, foods)
    return flask.jsonify(foods=foods)


@api_bp.get("/api/foods/<int:fdc_id>/measures")
def food_measure_suggestions(fdc_id):
    if not os.getenv("FDC_API_KEY"):
        return flask.jsonify(error="Food search is not configured"), 503
    try:
        food = get_food_client().get_food(fdc_id)
        return flask.jsonify(measures=food_measures(food))
    except Exception:
        return flask.jsonify(error="Serving sizes are temporarily unavailable."), 502


@api_bp.get("/api/exercises")
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

    save_exercise_search(query, exercises)
    return flask.jsonify(exercises=exercises)
