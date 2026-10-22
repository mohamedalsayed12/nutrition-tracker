"""Edge cases for barcode lookups, Siri logging, removed nutrients and protein targets."""
from types import SimpleNamespace

import pytest
import requests

import services.voice_log as voice_log
from database import db
from models import NutritionTargets
from routers import voice as voice_router
from services import barcode
from services.calc import apply_health_preferences
from services.nutrient_targets import UNTRACKED, micronutrient_targets
from services.voice_parser import SpokenItem, parse_meal_text


def n(name, unit, amount):
    return SimpleNamespace(name=name, unit_name=unit, amount=amount)


def p(description, grams):
    return SimpleNamespace(portion_description=description, gram_weight=grams, amount=1, modifier=None, measure_unit=None)


def usda(fdc_id, description, portions=(), kcal=100):
    return SimpleNamespace(fdc_id=fdc_id, description=description, data_type="SR Legacy", brand_name=None,
                           gtin_upc=None, nutrients=[n("Energy", "kcal", kcal)], food_portions=list(portions),
                           serving_size=None, serving_size_unit=None, household_serving_fulltext=None)


def sign_up(client, email):
    client.post("/api/v1/users", json={"name": "MK", "email": email, "password": "a-secure-password"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "a-secure-password"}).json["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.put("/api/v1/goals/nutrition", json={
        "age": 30, "sex": "female", "height_cm": 165, "weight_kg": 60,
        "activity_level": "lightly active", "goal": "maintain"}, headers=headers).status_code == 200
    return headers


# --- Open Food Facts over the network ----------------------------------------------------

class FakeResponse:
    def __init__(self, status, body=None):
        self.status_code, self.body = status, body

    def json(self):
        return self.body


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.sent = response, error, {}

    def get(self, url, params=None, headers=None, timeout=None):
        self.sent = {"url": url, "params": params, "headers": headers, "timeout": timeout}
        if self.error:
            raise self.error
        return self.response


def test_open_food_facts_request_identifies_the_app_and_reads_the_product():
    session = FakeSession(FakeResponse(200, {"status": 1, "product": {
        "product_name": "Beanz", "brands": "Heinz", "serving_quantity": 207, "serving_size": "1/2 can (207g)",
        "nutriments": {"energy-kcal_100g": 79, "proteins_100g": 4.7}}}))
    food = barcode.fetch_open_food_facts("5000157024671", session=session)
    assert food.description == "Beanz" and food.serving_size == 207
    assert session.sent["url"].endswith("/5000157024671.json")
    assert session.sent["headers"]["User-Agent"].startswith("health4everyone/")
    assert session.sent["timeout"] <= 10


@pytest.mark.parametrize("response", [FakeResponse(404), FakeResponse(200, {"status": 0}),
                                      FakeResponse(200, {"status": 1, "product": None})])
def test_unknown_barcodes_return_nothing(response):
    assert barcode.fetch_open_food_facts("5000000000000", session=FakeSession(response)) is None


@pytest.mark.parametrize("session", [FakeSession(error=requests.ConnectionError("down")), FakeSession(FakeResponse(503))])
def test_open_food_facts_outages_are_reported(session):
    with pytest.raises(LookupError):
        barcode.fetch_open_food_facts("5000157024671", session=session)


def test_usda_barcode_search_failure_is_treated_as_no_match():
    class Broken:
        def search(self, *args, **kwargs):
            raise RuntimeError("USDA down")
    assert barcode.find_usda_barcode(Broken(), "5000157024671") is None


# --- Siri amounts ------------------------------------------------------------------------------

MILK = usda(1, "Milk, whole", [p("1 cup", 244)], kcal=61)
OIL = usda(2, "Oil, olive", [p("1 tbsp", 13.5)], kcal=884)
WATER = usda(3, "Water, tap")
PIZZA = usda(4, "Pizza, cheese", [p("1 slice", 107)])


def grams(food, said):
    item = parse_meal_text(said)[1][0]
    return voice_log._grams(food, item)[0]


def test_millilitres_use_the_foods_own_density():
    assert grams(MILK, "250 ml of milk") == pytest.approx(250 * 244 / 236.588, rel=0.01)
    assert grams(WATER, "500 ml of water") == 500   # no USDA volume: 1 g per ml
    assert grams(MILK, "a litre of milk") == pytest.approx(1000 * 244 / 236.588, rel=0.01)


def test_spoken_units_match_usda_servings_or_fall_back_to_the_default():
    assert grams(OIL, "two tablespoons of olive oil") == 27
    assert grams(PIZZA, "3 slices of pizza") == 321
    assert grams(PIZZA, "a bowl of pizza") == 107          # no bowl serving: the usual serving
    assert grams(WATER, "a water") == 100                  # no servings at all: 100 g
    assert grams(MILK, "8 oz of milk") == pytest.approx(226.8, rel=0.001)


def test_siri_prefers_a_food_you_have_logged_before(monkeypatch):
    first, second = usda(10, "Yogurt, plain"), usda(11, "Yogurt, Greek, plain")
    monkeypatch.setattr(voice_log, "_find_foods", lambda client, query, raw_first=True: [first, second])
    monkeypatch.setattr(voice_log, "_previously_logged", lambda user_id, ids: {11})
    client = SimpleNamespace(get_food=lambda fdc_id: {10: first, 11: second}[fdc_id])
    item = SpokenItem(quantity=1, unit=None, food="yogurt", said="a yogurt")
    assert voice_log._match_food(1, client, item)[0].fdc_id == 11


def test_siri_skips_a_food_usda_cannot_return(monkeypatch):
    monkeypatch.setattr(voice_log, "_find_foods", lambda client, query, raw_first=True: [usda(12, "Yogurt, plain")])
    monkeypatch.setattr(voice_log, "_previously_logged", lambda user_id, ids: set())

    def broken(fdc_id):
        raise RuntimeError("USDA down")
    item = SpokenItem(quantity=1, unit=None, food="yogurt", said="a yogurt")
    assert voice_log._match_food(1, SimpleNamespace(get_food=broken), item) is None


# --- Siri keys -------------------------------------------------------------------------------

def test_siri_key_limit_and_bad_keys(client):
    headers = sign_up(client, "limit@example.com")
    for _ in range(5):
        assert client.post("/api/v1/api-tokens", json={"timezone": "UTC"}, headers=headers).status_code == 201
    too_many = client.post("/api/v1/api-tokens", json={"timezone": "UTC"}, headers=headers)
    assert too_many.status_code in (400, 409, 422)
    for bad in ("Bearer not-a-key", "Bearer h4e_wrong", "Basic abc"):
        assert client.post("/api/v1/voice-log", json={"text": "an egg"}, headers={"Authorization": bad}).status_code == 401


def test_voice_log_needs_food_search_configured(client, monkeypatch):
    headers = sign_up(client, "nokey@example.com")
    key = client.post("/api/v1/api-tokens", json={"timezone": "UTC"}, headers=headers).json["key"]

    def not_configured():
        raise ValueError("Food search is not configured.")
    monkeypatch.setattr(voice_router, "get_food_client", not_configured)
    response = client.post("/api/v1/voice-log", json={"text": "an egg"}, headers={"Authorization": f"Bearer {key}"})
    assert response.status_code == 503


# --- Removed nutrients ---------------------------------------------------------------------------

def test_removed_nutrients_are_not_targets_for_anyone():
    for age, sex, pregnant in ((25, "male", False), (30, "female", False), (30, "female", True), (70, "male", False)):
        names = {row["name"] for row in micronutrient_targets(age, sex, pregnant=pregnant)}
        assert not names & UNTRACKED
        assert len(names) == 23


def test_saved_targets_and_overrides_for_removed_nutrients_are_ignored(client, app):
    headers = sign_up(client, "untracked@example.com")
    with app.app_context():
        target = db.session.query(NutritionTargets).one()
        target.micronutrients = list(target.micronutrients) + [{"name": "Iodine", "unit": "mcg", "target": 150}]
        db.session.commit()
    shown = {row["name"] for row in client.get("/api/v1/goals/nutrition", headers=headers).json["micronutrients"]}
    assert "Iodine" not in shown
    saved = client.put("/api/v1/settings/health", json={"micronutrient_overrides": {"Iodine": 200, "Iron": 20}}, headers=headers)
    assert saved.status_code == 200, saved.json
    assert client.get("/api/v1/settings/health", headers=headers).json["micronutrient_overrides"] == {"Iron": 20}
    unknown = client.put("/api/v1/settings/health", json={"micronutrient_overrides": {"Unobtainium": 1}}, headers=headers)
    assert unknown.status_code in (400, 422)


# --- Protein with a care-plan calorie target ----------------------------------------------------------

def test_care_plan_calories_keep_the_weight_based_protein_minimum():
    nutrition = SimpleNamespace(age=30, sex="female", protein_min=0, protein_max=0, carbs=0, micronutrients=[])
    preferences = SimpleNamespace(conditions=[], custom_calories=1600, base_calories=2000, custom_carbs=None,
                                  custom_protein=None, custom_fat=None, base_carbs=275,
                                  base_protein_min=48.0, base_protein_max=175.0, micronutrient_overrides={})
    assert apply_health_preferences(nutrition, preferences) == 1600
    assert nutrition.protein_min == 48.0                 # 0.8 g/kg x 60 kg, unchanged by the care plan
    assert nutrition.protein_max == 140.0                # 35% of 1,600 kcal
    assert nutrition.carbs == 220.0                      # 55% of 1,600 kcal
