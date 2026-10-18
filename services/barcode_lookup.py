"""Resolve product barcodes to USDA foods for logging."""

import re

import requests

from services.food_search import _find_foods, get_food_client


def normalize_barcode(code):
    digits = re.sub(r"\D", "", str(code or ""))
    if not 8 <= len(digits) <= 14:
        raise ValueError("Enter a barcode with 8 to 14 digits.")
    return digits


def _serialize(food):
    return dict(
        fdc_id=food.fdc_id,
        description=food.description,
        data_type=food.data_type,
        brand_name=food.brand_name,
        gtin_upc=getattr(food, "gtin_upc", None),
    )


def _open_food_facts_name(barcode):
    try:
        response = requests.get(
            f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json",
            timeout=5,
            headers={"User-Agent": "NutritionTracker/1.0"},
        )
        if response.status_code != 200:
            return None
        payload = response.json()
        if payload.get("status") != 1:
            return None
        product = payload.get("product") or {}
        return (
            product.get("product_name")
            or product.get("generic_name")
            or product.get("abbreviated_product_name")
        )
    except (requests.RequestException, ValueError, TypeError):
        return None


def lookup_barcode(code):
    barcode = normalize_barcode(code)
    client = get_food_client()
    foods = _find_foods(client, barcode)
    source = "usda"
    hint = None
    if not foods:
        hint = _open_food_facts_name(barcode)
        if hint:
            foods = _find_foods(client, hint.lower())
            source = "open_food_facts_name"
    if not foods:
        raise ValueError("No matching food found for that barcode.")
    return dict(
        barcode=barcode,
        source=source,
        product_hint=hint,
        foods=[_serialize(food) for food in foods[:12]],
    )
