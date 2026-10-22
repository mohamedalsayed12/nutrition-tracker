"""Look up a packaged food by its barcode.

USDA's Branded Foods list is checked first, because its records are complete and
use the same format as every other food in the app. It mostly covers US
products, so when USDA has no match the product is looked up on Open Food Facts,
a free database with good coverage of UK and European supermarket products.

An Open Food Facts product is turned into the same shape as a USDA food (names,
units and amounts per 100 g), so serving sizes, logging, macro totals and
micronutrient targets all work on it unchanged.
"""

import logging
import re
from types import SimpleNamespace

import requests

logger = logging.getLogger(__name__)

OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/api/v2/product/{code}.json"
# Open Food Facts asks every app to identify itself.
USER_AGENT = "health4everyone/1.0 (https://github.com/mohamedalsayed12/nutrition-tracker)"
FIELDS = "code,product_name,product_name_en,generic_name,brands,nutriments,serving_quantity,serving_size,quantity"
SOURCE = "Open Food Facts"

# Open Food Facts nutriment -> (USDA nutrient name, USDA unit, factor from the OFF value).
# OFF stores "_100g" values in grams (or kcal for energy), so mg = g x 1000, mcg = g x 1,000,000.
NUTRIMENTS = (
    ("energy-kcal", "Energy", "kcal", 1),
    ("proteins", "Protein", "g", 1),
    ("carbohydrates", "Carbohydrate, by difference", "g", 1),
    ("fat", "Total lipid (fat)", "g", 1),
    ("fiber", "Fiber, total dietary", "g", 1),
    ("sugars", "Sugars, total including NLEA", "g", 1),
    ("saturated-fat", "Fatty acids, total saturated", "g", 1),
    ("sodium", "Sodium, Na", "mg", 1000),
    ("calcium", "Calcium, Ca", "mg", 1000),
    ("iron", "Iron, Fe", "mg", 1000),
    ("magnesium", "Magnesium, Mg", "mg", 1000),
    ("potassium", "Potassium, K", "mg", 1000),
    ("zinc", "Zinc, Zn", "mg", 1000),
    ("phosphorus", "Phosphorus, P", "mg", 1000),
    ("vitamin-c", "Vitamin C, total ascorbic acid", "mg", 1000),
    ("vitamin-b1", "Thiamin", "mg", 1000),
    ("vitamin-b2", "Riboflavin", "mg", 1000),
    ("vitamin-pp", "Niacin", "mg", 1000),
    ("vitamin-b6", "Vitamin B-6", "mg", 1000),
    ("vitamin-e", "Vitamin E (alpha-tocopherol)", "mg", 1000),
    ("vitamin-a", "Vitamin A, RAE", "µg", 1_000_000),
    ("vitamin-d", "Vitamin D (D2 + D3)", "µg", 1_000_000),
    ("vitamin-b12", "Vitamin B-12", "µg", 1_000_000),
    ("vitamin-k", "Vitamin K (phylloquinone)", "µg", 1_000_000),
    ("vitamin-b9", "Folate, DFE", "µg", 1_000_000),
    ("selenium", "Selenium, Se", "µg", 1_000_000),
)


def normalise_barcode(value):
    """Digits only, 8 to 14 long (EAN-8, UPC-A, EAN-13, GTIN-14), or None."""
    digits = re.sub(r"\D", "", str(value or ""))
    return digits if 8 <= len(digits) <= 14 else None


def same_barcode(a, b):
    """UPC-A (12 digits) and EAN-13 (13) are the same code with a leading zero."""
    return bool(a) and bool(b) and a.lstrip("0") == b.lstrip("0")


def find_usda_barcode(client, code):
    try:
        results = client.search(code, page_size=50).foods
    except Exception:
        logger.warning("USDA barcode search failed", exc_info=True)
        return None
    return next((food for food in results if same_barcode(getattr(food, "gtin_upc", None), code)), None)


def fetch_open_food_facts(code, session=requests):
    """The product as a USDA-shaped food, or None when it is unknown or has no nutrition data."""
    try:
        response = session.get(OPEN_FOOD_FACTS_URL.format(code=code), params={"fields": FIELDS},
                               headers={"User-Agent": USER_AGENT}, timeout=8)
    except requests.RequestException:
        logger.warning("Open Food Facts lookup failed", exc_info=True)
        raise LookupError("Barcode lookup is temporarily unavailable.") from None
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise LookupError("Barcode lookup is temporarily unavailable.")
    data = response.json()
    if data.get("status") != 1 or not data.get("product"):
        return None
    return open_food_facts_food(code, data["product"])


def open_food_facts_food(code, product):
    nutriments = product.get("nutriments") or {}
    nutrients = []
    for key, name, unit, factor in NUTRIMENTS:
        value = _number(nutriments.get(f"{key}_100g"))
        if value is None and key == "energy-kcal":
            kj = _number(nutriments.get("energy-kj_100g") or nutriments.get("energy_100g"))
            value = round(kj / 4.184, 1) if kj is not None else None
        if value is None and key == "sodium":
            salt = _number(nutriments.get("salt_100g"))
            value = salt / 2.5 if salt is not None else None  # salt is 40% sodium
        if value is not None:
            nutrients.append(SimpleNamespace(name=name, unit_name=unit, amount=round(value * factor, 4)))
    if not any(n.name == "Energy" for n in nutrients):
        return None  # without calories the product can't be logged meaningfully
    name = (product.get("product_name_en") or product.get("product_name") or product.get("generic_name") or "").strip()
    brand = (product.get("brands") or "").split(",")[0].strip() or None
    serving_grams = _number(product.get("serving_quantity"))
    return SimpleNamespace(
        fdc_id=None,
        barcode=code,
        description=name or f"Product {code}",
        brand_name=brand,
        data_type=SOURCE,
        gtin_upc=code,
        nutrients=nutrients,
        food_portions=[],
        serving_size=serving_grams if serving_grams and serving_grams > 0 else None,
        serving_size_unit="g" if serving_grams and serving_grams > 0 else None,
        household_serving_fulltext=_serving_label(product.get("serving_size")),
    )


def _serving_label(text):
    """"1 bar (45 g)" -> "1 bar"; the grams are added to the label separately."""
    text = re.sub(r"\s*\(.*?\)\s*", " ", str(text or "")).strip()
    return text or None


def _number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None
