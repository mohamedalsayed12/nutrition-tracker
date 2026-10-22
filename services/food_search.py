import os
import re

import requests
from flask import abort
from usda_fdc import FdcClient, FdcResourceNotFoundError

from database import db
from models import FoodLog
from services.food_ranking import rank_foods, words


def get_food_client():
    api_key = os.getenv("FDC_API_KEY")
    if not api_key:
        raise ValueError("Food search is not configured.")
    return FdcClient(api_key)


GENERIC_TYPES = ["Foundation", "SR Legacy", "Survey (FNDDS)"]


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

    # Generic and branded foods are fetched separately so the thousands of branded
    # products cannot crowd everyday foods out of the results.
    generic = client.search(query, data_type=GENERIC_TYPES, page_size=100).foods
    branded = client.search(query, data_type=["Branded"], page_size=50).foods
    ranked = rank_foods(list(generic) + list(branded), query)
    query_words = words(query)
    if len(query_words) > 1 and sum(food.data_type != "Branded" for food in ranked) < 5:
        # A multi-word search can miss foods USDA indexes differently, so widen
        # the generic search to the first word and keep only full matches.
        broader = client.search(query_words[0], data_type=GENERIC_TYPES, page_size=100).foods
        ranked = rank_foods(list(generic) + list(broader) + list(branded), query)
    return ranked


def search_foods(query, user_id=None):
    if len(query) < 2:
        return []
    if len(query) > 80:
        abort(400, description="Search is too long.")
    if not os.getenv("FDC_API_KEY"):
        abort(503, description="Food search is not configured.")
    try:
        ordered = _find_foods(get_food_client(), query)
    except Exception:
        abort(502, description="Food search is temporarily unavailable.")
    logged = _previously_logged(user_id, [food.fdc_id for food in ordered])
    # Like Cronometer, foods you have logged before come first; the rest keep their ranking.
    ordered = sorted(ordered, key=lambda food: food.fdc_id not in logged)
    return [dict(fdc_id=food.fdc_id, description=food.description,
                 data_type=food.data_type, brand_name=food.brand_name,
                 gtin_upc=getattr(food, "gtin_upc", None),
                 previously_logged=food.fdc_id in logged) for food in ordered]


def _previously_logged(user_id, fdc_ids):
    if user_id is None or not fdc_ids:
        return set()
    rows = db.session.query(FoodLog.fdc_id).filter(
        FoodLog.user_id == user_id, FoodLog.fdc_id.in_(fdc_ids)).distinct()
    return {fdc_id for (fdc_id,) in rows}


def search_exercises(query):
    if len(query) < 2:
        return []
    if len(query) > 80:
        abort(400, description="Search is too long.")
    api_key = os.getenv("API_NINJAS_KEY")
    if not api_key:
        abort(503, description="Exercise search is not configured.")
    try:
        response = requests.get("https://api.api-ninjas.com/v1/exercises",
                                params={"name": query}, headers={"X-Api-Key": api_key}, timeout=5)
        response.raise_for_status()
        return [item["name"] for item in response.json()]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        abort(502, description="Exercise search is temporarily unavailable.")
