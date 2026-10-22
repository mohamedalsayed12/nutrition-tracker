from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

import routers.foods as foods_router
import services.logs as logs
import services.voice_log as voice_log
from routers import voice as voice_router
from services import barcode, food_search
from services.food_ranking import rank_foods
from services.voice_log import meal_for_time, spoken_reply
from services.voice_parser import parse_meal_text


def n(name, unit, amount):
    return SimpleNamespace(name=name, unit_name=unit, amount=amount)


def p(description, grams):
    return SimpleNamespace(portion_description=description, gram_weight=grams, amount=1, modifier=None, measure_unit=None)


def usda(fdc_id, description, nutrients, portions=(), data_type="SR Legacy", gtin=None):
    return SimpleNamespace(fdc_id=fdc_id, description=description, data_type=data_type, brand_name=None,
                           gtin_upc=gtin, nutrients=nutrients, food_portions=list(portions),
                           serving_size=None, serving_size_unit=None, household_serving_fulltext=None)


# Real USDA values per 100 g.
EGG = usda(171287, "Egg, whole, raw, fresh", [n("Energy", "kcal", 143), n("Protein", "g", 12.6)],
           [p("1 large", 50), p("1 medium", 44)])
BANANA = usda(173944, "Bananas, raw", [n("Energy", "kcal", 89), n("Potassium, K", "mg", 358)],
              [p("1 medium (7\" to 7-7/8\" long)", 118), p("1 large (8\" to 8-7/8\" long)", 136), p("1 cup, sliced", 150)])
MILK = usda(2705385, "Milk, whole", [n("Energy", "kcal", 61), n("Calcium, Ca", "mg", 123)],
            [p("Guideline amount per fl oz of beverage", 2.5), p("1 cup", 244)], data_type="Survey (FNDDS)")
TOAST = usda(174930, "Bread, white, toasted", [n("Energy", "kcal", 293)], [p("1 slice", 22)])
CEREAL = usda(9001, "Oat cereal", [n("Energy", "kcal", 380)], data_type="Branded", gtin="0012345678905")
FOODS = [EGG, BANANA, MILK, TOAST, CEREAL]


class FakeUsda:
    def get_food(self, fdc_id):
        return next(food for food in FOODS if food.fdc_id == fdc_id)

    def search(self, query, page_size=50, data_type=None, **kwargs):
        foods = [food for food in FOODS if not data_type or food.data_type in data_type]
        return SimpleNamespace(foods=foods)


@pytest.fixture
def fake_usda(monkeypatch):
    monkeypatch.setenv("FDC_API_KEY", "test-key")
    for module in (food_search, foods_router, logs, voice_router):
        monkeypatch.setattr(module, "get_food_client", FakeUsda)
    return FakeUsda()


def sign_up(client, email="voice@example.com"):
    client.post("/api/v1/users", json={"name": "MK", "email": email, "password": "a-secure-password"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "a-secure-password"}).json["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.put("/api/v1/goals/nutrition", json={
        "age": 22, "sex": "male", "height_cm": 180, "weight_kg": 80,
        "activity_level": "moderately active", "goal": "maintain"}, headers=headers).status_code == 200
    return headers


# --- Open Food Facts ------------------------------------------------------------

# A real-shaped Open Food Facts product (values per 100 g, minerals in grams).
OFF_PRODUCT = {
    "product_name": "Greek Style Natural Yogurt", "brands": "Tesco, Tesco Finest",
    "serving_size": "1 pot (150 g)", "serving_quantity": "150",
    "nutriments": {"energy-kcal_100g": 113, "proteins_100g": 5.1, "carbohydrates_100g": 5.4,
                   "fat_100g": 7.9, "sugars_100g": 5.4, "salt_100g": 0.15,
                   "calcium_100g": 0.15, "vitamin-d_100g": 0.0000012},
}


def test_open_food_facts_product_becomes_a_usda_shaped_food():
    food = barcode.open_food_facts_food("5051234567890", OFF_PRODUCT)
    values = {item.name: (item.amount, item.unit_name) for item in food.nutrients}
    assert food.description == "Greek Style Natural Yogurt"
    assert food.brand_name == "Tesco"
    assert values["Energy"] == (113, "kcal")
    assert values["Protein"] == (5.1, "g")
    assert values["Sodium, Na"] == (60, "mg")            # 0.15 g salt = 60 mg sodium
    assert values["Calcium, Ca"] == (150, "mg")
    assert values["Vitamin D (D2 + D3)"] == (1.2, "µg")
    assert food.serving_size == 150
    assert food.household_serving_fulltext == "1 pot"


def test_energy_from_kilojoules_and_products_without_calories_are_rejected():
    food = barcode.open_food_facts_food("5051234567890", {"product_name": "Water", "nutriments": {"energy-kj_100g": 418.4}})
    assert next(item.amount for item in food.nutrients if item.name == "Energy") == 100
    assert barcode.open_food_facts_food("5051234567890", {"product_name": "Mystery", "nutriments": {}}) is None


def test_barcode_digits_and_upc_ean_equivalence():
    assert barcode.normalise_barcode(" 5051-2345 67890 ") == "5051234567890"
    assert barcode.normalise_barcode("1234") is None
    assert barcode.same_barcode("012345678905", "0012345678905")


def test_barcode_route_prefers_usda_then_falls_back_to_open_food_facts(client, fake_usda, monkeypatch):
    found = client.get("/api/v1/foods/barcode/012345678905")
    assert found.status_code == 200
    assert found.json["food"]["fdc_id"] == 9001
    assert found.json["food"]["source"] == "USDA"

    monkeypatch.setattr(foods_router, "fetch_open_food_facts",
                        lambda code: barcode.open_food_facts_food(code, OFF_PRODUCT))
    off = client.get("/api/v1/foods/barcode/5051234567890")
    assert off.status_code == 200
    assert off.json["food"]["barcode"] == "5051234567890"
    assert off.json["food"]["source"] == "Open Food Facts"
    assert off.json["food"]["kcal_per_100g"] == 113
    default = next(m for m in off.json["measures"] if m["default"])
    assert default["label"] == "1 pot (150 g)"

    monkeypatch.setattr(foods_router, "fetch_open_food_facts", lambda code: None)
    assert client.get("/api/v1/foods/barcode/5050000000000").status_code == 404
    assert client.get("/api/v1/foods/barcode/12").status_code == 400


def test_logging_an_open_food_facts_product(client, fake_usda, monkeypatch):
    headers = sign_up(client, "barcode@example.com")
    monkeypatch.setattr(logs, "fetch_open_food_facts", lambda code: barcode.open_food_facts_food(code, OFF_PRODUCT))
    created = client.post("/api/v1/food-logs", json={"meal": "snack", "barcode": "5051234567890", "grams": 150},
                          headers=headers)
    assert created.status_code == 201, created.json
    assert created.json["fdc_id"] is None
    assert created.json["barcode"] == "5051234567890"
    assert created.json["food_name"] == "Greek Style Natural Yogurt (Tesco)"
    report = client.get("/api/v1/reports/daily", headers=headers).json
    assert report["totals"]["Calories"] == pytest.approx(169.5)
    frequent = client.get("/api/v1/foods/frequent", headers=headers).json
    assert frequent["foods"]["snack"][0]["barcode"] == "5051234567890"
    both = client.post("/api/v1/food-logs", json={"meal": "snack", "barcode": "5051234567890", "fdc_id": 1, "grams": 1},
                       headers=headers)
    assert both.status_code in (400, 422)


# --- Siri: parsing ------------------------------------------------------------------

@pytest.mark.parametrize("said, meal, items", [
    ("I had two scrambled eggs, a slice of toast and 250 ml of milk for breakfast", "breakfast",
     [(2, None, "scrambled eggs"), (1, "slice", "toast"), (250, "ml", "milk")]),
    ("Hey Siri log a medium banana", None, [(1, "medium", "banana")]),
    ("fish and chips for dinner", "dinner", [(None, None, "fish and chips")]),
    ("200g chicken breast and a cup of rice for lunch", "lunch", [(200, "g", "chicken breast"), (1, "cup", "rice")]),
    ("one and a half cups of milk", None, [(1.5, "cup", "milk")]),
    ("2 1/2 slices of bread", None, [(2.5, "slice", "bread")]),
    ("a 330ml can of coke", None, [(330, "ml", "coke")]),
    ("a cup of tea and two biscuits", None, [(1, "cup", "tea"), (2, None, "biscuits")]),
    ("Lunch: a tuna sandwich", "lunch", [(1, None, "tuna sandwich")]),
    ("some almonds as a snack", "snack", [(None, None, "almonds")]),
])
def test_spoken_sentences_are_understood(said, meal, items):
    parsed_meal, parsed = parse_meal_text(said)
    assert parsed_meal == meal
    assert [(item.quantity, item.unit, item.food) for item in parsed] == items


def test_meal_from_the_time_of_day():
    london = ZoneInfo("Europe/London")
    assert meal_for_time(datetime(2026, 10, 22, 8, tzinfo=london)) == "breakfast"
    assert meal_for_time(datetime(2026, 10, 22, 13, tzinfo=london)) == "lunch"
    assert meal_for_time(datetime(2026, 10, 22, 19, tzinfo=london)) == "dinner"
    assert meal_for_time(datetime(2026, 10, 22, 23, tzinfo=london)) == "snack"


# --- Siri: keys and logging ------------------------------------------------------------

def test_siri_keys_are_shown_once_and_can_only_log_food(client):
    headers = sign_up(client, "keys@example.com")
    created = client.post("/api/v1/api-tokens", json={"name": "iPhone", "timezone": "Europe/London"}, headers=headers)
    assert created.status_code == 201
    key = created.json["key"]
    assert key.startswith("h4e_")
    listed = client.get("/api/v1/api-tokens", headers=headers).json["tokens"]
    assert listed[0]["name"] == "iPhone" and "key" not in listed[0]
    siri = {"Authorization": f"Bearer {key}"}
    assert client.get("/api/v1/reports/daily", headers=siri).status_code in (401, 422)  # not a sign-in token
    assert client.post("/api/v1/voice-log", json={"text": "an egg"}).status_code == 401
    assert client.post("/api/v1/api-tokens", json={"timezone": "Not/AZone"}, headers=headers).status_code == 422
    assert client.delete(f"/api/v1/api-tokens/{listed[0]['id']}", headers=headers).status_code == 204
    assert client.post("/api/v1/voice-log", json={"text": "an egg"}, headers=siri).status_code == 401


def test_siri_logs_foods_with_usda_servings_and_reports_calories_left(client, fake_usda):
    headers = sign_up(client, "siri@example.com")
    key = client.post("/api/v1/api-tokens", json={"timezone": "Europe/London"}, headers=headers).json["key"]
    response = client.post("/api/v1/voice-log", headers={"Authorization": f"Bearer {key}"}, json={
        "text": "I had two eggs, a medium banana, a slice of toast and a cup of milk for breakfast"})
    assert response.status_code == 201, response.json
    body = response.json
    assert body["meal"] == "breakfast"
    logged = {item["food_name"]: item for item in body["logged"]}
    assert logged["Egg, whole, raw, fresh"]["grams"] == 88         # 2 x the default (medium, 44 g)
    assert logged["Bananas, raw"]["grams"] == 118                  # USDA medium banana
    assert logged["Bread, white, toasted"]["grams"] == 22          # 1 slice
    assert logged["Milk, whole"]["grams"] == 244                   # 1 cup, not the 2.5 g guideline amount
    expected_kcal = round(143 * 0.88 + 89 * 1.18 + 293 * 0.22 + 61 * 2.44)
    assert sum(item["kcal"] for item in body["logged"]) == pytest.approx(expected_kcal, abs=2)
    assert body["calories_left"] == pytest.approx(body["calorie_target"] - body["calories_today"], abs=1)
    assert body["spoken"].startswith("Logged two eggs, a medium banana, a slice of toast and a cup of milk to breakfast")
    assert "calories left today" in body["spoken"]
    report = client.get("/api/v1/reports/daily", headers=headers).json
    assert report["food_log_count"] == 4


def test_siri_says_what_it_could_not_find(client, fake_usda):
    headers = sign_up(client, "siri2@example.com")
    key = client.post("/api/v1/api-tokens", json={"timezone": "UTC"}, headers=headers).json["key"]
    body = client.post("/api/v1/voice-log", headers={"Authorization": f"Bearer {key}"},
                       json={"text": "an egg and a dragonfruit smoothie", "meal": "snack"}).json
    assert [item["food_name"] for item in body["logged"]] == ["Egg, whole, raw, fresh"]
    assert body["not_found"] == ["a dragonfruit smoothie"]
    assert "couldn't find a dragonfruit smoothie" in body["spoken"]


def test_spoken_reply_when_nothing_was_heard():
    assert "didn't catch" in spoken_reply("lunch", [], [], 1500)


# --- Raw foods first in search ----------------------------------------------------------------

def test_search_shows_raw_foods_before_cooked_and_branded():
    foods = [SimpleNamespace(fdc_id=1, description="Rice, cooked, NFS", data_type="Survey (FNDDS)", brand_name=None, gtin_upc=None),
             SimpleNamespace(fdc_id=2, description="Rice, white, long-grain, regular, raw, enriched", data_type="SR Legacy", brand_name=None, gtin_upc=None),
             SimpleNamespace(fdc_id=3, description="RICE", data_type="Branded", brand_name="Store", gtin_upc=None),
             SimpleNamespace(fdc_id=4, description="Rice, brown, long-grain, raw", data_type="SR Legacy", brand_name=None, gtin_upc=None)]
    search_order = [food.fdc_id for food in rank_foods(foods, "rice")]
    assert search_order[:2] in ([2, 4], [4, 2])
    assert search_order[-1] == 3


def test_siri_picks_cooked_rice_but_raw_banana(client, monkeypatch):
    rice_raw = usda(2, "Rice, white, long-grain, regular, raw, enriched", [n("Energy", "kcal", 365)], [p("1 cup", 185)])
    rice_cooked = usda(1, "Rice, cooked, NFS", [n("Energy", "kcal", 129)], [p("1 cup, cooked", 158)], data_type="Survey (FNDDS)")
    monkeypatch.setattr(voice_log, "_find_foods", lambda client, query, raw_first=True:
                        [rice_raw, rice_cooked] if "rice" in query else [BANANA])
    client_stub = SimpleNamespace(get_food=lambda fdc_id: {1: rice_cooked, 2: rice_raw, BANANA.fdc_id: BANANA}[fdc_id])
    monkeypatch.setattr(voice_log, "_previously_logged", lambda user_id, ids: set())
    rice = voice_log._match_food(1, client_stub, parse_meal_text("a cup of rice")[1][0])
    assert rice[0].description == "Rice, cooked, NFS" and rice[1] == 158
    banana = voice_log._match_food(1, client_stub, parse_meal_text("a banana")[1][0])
    assert banana[0].description == "Bananas, raw"


def test_voice_log_uses_cooked_order(monkeypatch):
    calls = {}

    def fake_find(client, query, raw_first=True):
        calls["raw_first"] = raw_first
        return []
    monkeypatch.setattr(voice_log, "_find_foods", fake_find)
    item = parse_meal_text("a cup of rice")[1][0]
    assert voice_log._match_food(1, None, item) is None
    assert calls["raw_first"] is False


