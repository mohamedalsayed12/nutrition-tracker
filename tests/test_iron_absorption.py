from types import SimpleNamespace

from services.iron_absorption import iron_absorption_checks


def food(meal, iron_mg=None, vitamin_c_mg=None, iron_unit="mg"):
    nutrients = [{"name": "Energy", "unit": "kcal", "eaten": 200}]
    if iron_mg is not None:
        nutrients.append({"name": "Iron, Fe", "unit": iron_unit, "eaten": iron_mg})
    if vitamin_c_mg is not None:
        nutrients.append({"name": "Vitamin C, total ascorbic acid", "unit": "mg", "eaten": vitamin_c_mg})
    return SimpleNamespace(meal=meal, nutrients=nutrients)


def test_meal_with_iron_and_little_vitamin_c_gets_a_tip():
    checks = iron_absorption_checks([food("lunch", iron_mg=4.2, vitamin_c_mg=3)])
    assert checks == [{
        "meal": "lunch", "iron_mg": 4.2, "vitamin_c_mg": 3.0, "status": "add_vitamin_c",
        "tip": checks[0]["tip"], "highlight": False,
    }]
    assert "4.2 mg of iron" in checks[0]["tip"]


def test_vitamin_c_counts_only_within_the_same_meal():
    logs = [food("breakfast", iron_mg=0.5, vitamin_c_mg=80),   # orange juice at breakfast
            food("dinner", iron_mg=3.0, vitamin_c_mg=0),        # lentils at dinner
            food("dinner", iron_mg=1.0, vitamin_c_mg=5)]
    checks = iron_absorption_checks(logs)
    assert [(c["meal"], c["status"]) for c in checks] == [("dinner", "add_vitamin_c")]
    assert checks[0]["iron_mg"] == 4.0
    assert checks[0]["vitamin_c_mg"] == 5.0


def test_meal_that_pairs_iron_with_vitamin_c_is_marked_good():
    logs = [food("dinner", iron_mg=3.5, vitamin_c_mg=0), food("dinner", vitamin_c_mg=40)]
    assert iron_absorption_checks(logs)[0]["status"] == "good"


def test_meals_with_little_iron_or_no_iron_data_are_skipped():
    logs = [food("snack", iron_mg=0.8, vitamin_c_mg=0), food("breakfast")]
    assert iron_absorption_checks(logs) == []


def test_units_are_converted_and_missing_vitamin_c_data_is_reported_as_none():
    checks = iron_absorption_checks([food("lunch", iron_mg=2500, iron_unit="ug")])
    assert checks[0]["iron_mg"] == 2.5
    assert checks[0]["vitamin_c_mg"] is None
    assert checks[0]["status"] == "add_vitamin_c"


def test_periods_highlight_the_tip():
    checks = iron_absorption_checks([food("lunch", iron_mg=4, vitamin_c_mg=0)], ["menstruation"])
    assert checks[0]["highlight"] is True


def test_daily_report_includes_meal_checks(client, monkeypatch):
    lentils = SimpleNamespace(description="Lentils, cooked", nutrients=[
        SimpleNamespace(name="Energy", unit_name="kcal", amount=116),
        SimpleNamespace(name="Iron, Fe", unit_name="mg", amount=3.3),
        SimpleNamespace(name="Vitamin C, total ascorbic acid", unit_name="mg", amount=1.5),
    ])
    monkeypatch.setattr("services.logs.get_food_client",
                        lambda: SimpleNamespace(get_food=lambda _: lentils))
    client.post("/api/v1/users", json={
        "name": "Test User", "email": "iron@example.com", "password": "a-secure-password"})
    token = client.post("/api/v1/auth/login", json={
        "email": "iron@example.com", "password": "a-secure-password"}).json["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/reports/daily", headers=headers).json["iron_absorption"] == []
    assert client.post("/api/v1/food-logs", json={"meal": "dinner", "fdc_id": 1, "grams": 200},
                       headers=headers).status_code == 201
    checks = client.get("/api/v1/reports/daily", headers=headers).json["iron_absorption"]
    assert [(c["meal"], c["status"], c["iron_mg"]) for c in checks] == [("dinner", "add_vitamin_c", 6.6)]
