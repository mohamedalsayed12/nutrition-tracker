"""Turn a spoken sentence into a food log for in-app voice and external assistants."""

import os

from flask import abort

from services.food_search import search_foods
from services.logs import create_food, serialize_food
from services.voice_parse import parse_voice_log
from schemas import FoodLogCreate


def voice_log_for_user(user_id, transcript, default_meal="snack", auto_log=True):
    parsed = parse_voice_log(transcript, default_meal=default_meal)
    if not os.getenv("FDC_API_KEY"):
        abort(503, description="Food search is not configured.")
    foods = search_foods(parsed["food_query"])
    if not foods:
        raise ValueError(
            f'No USDA match for “{parsed["food_query"]}”. Try a clearer food name.'
        )
    best = foods[0]
    result = dict(
        **parsed,
        foods=foods,
        selected=best,
        logged=None,
    )
    if not auto_log:
        return result
    log = create_food(
        user_id,
        FoodLogCreate(meal=parsed["meal"], fdc_id=best["fdc_id"], grams=parsed["grams"]),
    )
    result["logged"] = serialize_food(log)
    return result
