import logging
import os
import re
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

import requests
from flask import abort
from usda_fdc import FdcClient, FdcResourceNotFoundError
from usda_fdc.models import SearchResult

from database import db
from models import FoodLog
from services.food_ranking import rank_foods, words

logger = logging.getLogger(__name__)


class FoodClient(FdcClient):
    """The USDA client, sending searches that filter by data type as POST.

    USDA's server rejects some GET searches that filter by data type (an nginx
    400 for queries such as "apple"), while the same search sent as a POST with
    a JSON body works, so filtered searches use POST.
    """

    def search(self, query, data_type=None, page_size=50, page_number=1, **kwargs):
        key = ("search", query.lower().strip(), tuple(data_type or ()), page_size, page_number)
        return _cache.get_or_set(key, lambda: self._search(query, data_type, page_size, page_number, **kwargs))

    def _search(self, query, data_type, page_size, page_number, **kwargs):
        if not data_type:
            return super().search(query, page_size=page_size, page_number=page_number, **kwargs)
        data = self._make_request("foods/search", method="POST", data={
            "query": query, "dataType": list(data_type),
            "pageSize": page_size, "pageNumber": page_number,
        })
        return SearchResult.from_api_data(data)

    def get_food(self, fdc_id, *args, **kwargs):
        return _cache.get_or_set(("food", int(fdc_id)), lambda: super(FoodClient, self).get_food(fdc_id, *args, **kwargs))


class _TtlCache:
    """A small in-memory cache for USDA answers.

    USDA's data changes a few times a year, so repeating a search or opening the
    same food again within hours is served from memory instead of a second
    round trip (each one takes 0.5-1 s). Failures are not cached.
    """

    def __init__(self, max_items=3000, ttl_seconds=12 * 3600):
        self.max_items, self.ttl = max_items, ttl_seconds
        self.items = OrderedDict()
        self.lock = threading.Lock()

    def get_or_set(self, key, compute):
        now = time.monotonic()
        with self.lock:
            hit = self.items.get(key)
            if hit is not None and now - hit[0] < self.ttl:
                self.items.move_to_end(key)
                return hit[1]
        value = compute()
        with self.lock:
            self.items[key] = (now, value)
            self.items.move_to_end(key)
            while len(self.items) > self.max_items:
                self.items.popitem(last=False)
        return value

    def clear(self):
        with self.lock:
            self.items.clear()


_cache = _TtlCache()
# The three searches for one query (lab-analysed, survey, branded) run at the same time.
_pool = ThreadPoolExecutor(max_workers=6, thread_name_prefix="usda")


def get_food_client():
    api_key = os.getenv("FDC_API_KEY")
    if not api_key:
        raise ValueError("Food search is not configured.")
    return FoodClient(api_key)


GENERIC_TYPES = ["Foundation", "SR Legacy", "Survey (FNDDS)"]


# Everyday and British words -> the words USDA uses in its names.
SYNONYMS = {
    "toast": "bread toasted", "toasts": "bread toasted",
    "crisps": "potato chips", "crisp": "potato chips",
    "chips": "french fries", "chip": "french fries",
    "biscuit": "cookies", "biscuits": "cookies",
    "porridge": "oatmeal cooked", "mince": "ground beef", "minced beef": "ground beef",
    "prawn": "shrimp", "prawns": "shrimp", "courgette": "zucchini", "courgettes": "zucchini",
    "aubergine": "eggplant", "aubergines": "eggplant", "coriander": "cilantro",
    "coke": "cola", "fizzy drink": "soft drink", "yoghurt": "yogurt", "yoghurts": "yogurt",
    "jam": "jams and preserves", "rocket": "arugula", "spring onion": "scallions",
    "spring onions": "scallions", "jacket potato": "potato baked", "beetroot": "beets",
    "swede": "rutabaga", "mangetout": "snow peas", "single cream": "cream light",
    "double cream": "cream heavy", "icing sugar": "sugar powdered", "cornflour": "cornstarch",
}


def with_synonyms(query):
    return SYNONYMS.get(query.strip().lower(), query)


def _find_foods(client, query, raw_first=True):
    query = with_synonyms(query)
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
    # products cannot crowd everyday foods out of the results. If USDA rejects the
    # filtered searches, fall back to one unfiltered search rather than failing.
    try:
        # Lab-analysed foods (SR Legacy, Foundation) are fetched on their own: they
        # hold the plain raw entries ("Rice, white, long-grain, raw"), which USDA's
        # relevance order otherwise pushes behind dozens of Survey dishes.
        jobs = [_pool.submit(client.search, query, data_type=types, page_size=size)
                for types, size in ((["SR Legacy", "Foundation"], 60), (["Survey (FNDDS)"], 60), (["Branded"], 25))]
        analysed, survey, branded = (list(job.result(timeout=20).foods) for job in jobs)
        generic = analysed + survey
    except Exception:
        logger.warning("Filtered USDA search failed; using an unfiltered search", exc_info=True)
        generic, branded = list(client.search(query, page_size=100).foods), []
    ranked = rank_foods(generic + branded, query, raw_first)
    query_words = words(query)
    if len(query_words) > 1 and sum(food.data_type != "Branded" for food in ranked) < 5:
        # A multi-word search can miss foods USDA indexes differently, so widen
        # the search to the first word and keep only full matches.
        try:
            broader = list(client.search(query_words[0], data_type=GENERIC_TYPES, page_size=100).foods)
        except Exception:
            broader = list(client.search(query_words[0], page_size=100).foods)
        ranked = rank_foods(generic + broader + branded, query, raw_first)
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
