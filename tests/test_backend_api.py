from types import SimpleNamespace
from datetime import datetime, timezone

PROFILE = {
    "age": 30, "sex": "male", "height_cm": 175, "weight_kg": 75,
    "activity_level": "moderately active",
}


def register_and_login(client, email, **profile_overrides):
    payload = {
        "name": "Test User", "email": email, "password": "a-secure-password",
        **PROFILE, **profile_overrides,
    }
    registration = client.post("/api/v1/users", json=payload)
    assert registration.status_code == 201, registration.json
    login = client.post("/api/v1/auth/login", json={
        "email": email, "password": "a-secure-password",
    })
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json['access_token']}"}


def test_auth_and_private_profile(client):
    assert client.get("/api/v1/users/me").status_code == 401
    first = register_and_login(client, "first@example.com")
    me = client.get("/api/v1/users/me", headers=first).json
    assert me["email"] == "first@example.com"
    assert me["needs_goal"] is True
    assert me["profile"]["weight_kg"] == 75
    assert client.post("/api/v1/users", json={
        "name": "Other", "email": "first@example.com", "password": "a-secure-password",
        **PROFILE,
    }).status_code == 409
    assert client.post("/api/v1/auth/login", json={
        "email": "first@example.com", "password": "wrong-password",
    }).status_code == 401


def test_registration_then_goal_sets_calories_and_macros(client):
    headers = register_and_login(client, "goal@example.com", sex="female", weight_kg=60, height_cm=165)
    me = client.get("/api/v1/users/me", headers=headers).json
    assert me["needs_goal"] is True
    response = client.put("/api/v1/goals/goal", headers=headers, json={"goal": "lose_weight"})
    assert response.status_code == 200
    assert response.json["calories"] > 0
    assert response.json["protein_min"] > 0
    assert response.json["carbs"] > 0
    assert response.json["goal"] == "lose_weight"
    me = client.get("/api/v1/users/me", headers=headers).json
    assert me["needs_goal"] is False
    assert me["nutrition_configured"] is True
    daily = client.get("/api/v1/reports/daily", headers=headers).json
    assert daily["calorie_goal"] == response.json["calories"]
    names = {row["name"] for row in daily["progress"]}
    assert {"Calories", "Protein", "Carbohydrates"}.issubset(names)


def test_food_logs_are_scoped_to_owner_and_summarized(client, monkeypatch):
    food = SimpleNamespace(description="Oats", nutrients=[
        SimpleNamespace(name="Energy", unit_name="kcal", amount=380),
        SimpleNamespace(name="Protein", unit_name="g", amount=13),
    ])
    monkeypatch.setattr("services.logs.get_food_client", lambda: SimpleNamespace(get_food=lambda _: food))
    first = register_and_login(client, "first@example.com")
    second = register_and_login(client, "second@example.com")
    response = client.post("/api/v1/food-logs", json={
        "meal": "breakfast", "fdc_id": 123, "grams": 50,
    }, headers=first)
    assert response.status_code == 201
    log_id = response.json["id"]
    assert response.json["nutrients"][0]["eaten"] == 190
    assert client.get("/api/v1/food-logs", headers=first).json["total"] == 1
    assert client.get("/api/v1/food-logs", headers=second).json["total"] == 0
    assert client.get(f"/api/v1/food-logs/{log_id}", headers=second).status_code == 404
    assert client.delete(f"/api/v1/food-logs/{log_id}", headers=second).status_code == 404
    assert client.put("/api/v1/goals/calories", json={"calories": 2000}, headers=first).status_code == 200
    summary = client.get("/api/v1/reports/daily", headers=first).json
    assert summary["totals"]["Calories"] == 190
    assert summary["calorie_goal"] == 2000
    day = datetime.now(timezone.utc).date().isoformat()
    assert client.put(f"/api/v1/days/{day}/save", headers=first).status_code == 200
    assert client.get("/api/v1/days", headers=first).json["days"] == [day]
    payload = {"meal": "breakfast", "fdc_id": 123, "grams": 100}
    assert client.put(f"/api/v1/food-logs/{log_id}", json=payload, headers=second).status_code == 404
    assert client.put(f"/api/v1/food-logs/{log_id}", json=payload, headers=first).status_code == 200
    assert client.get("/api/v1/days", headers=first).json["days"] == []
    assert client.delete(f"/api/v1/food-logs/{log_id}", headers=first).status_code == 204


def test_food_log_validation_and_pagination(client):
    headers = register_and_login(client, "first@example.com")
    assert client.post("/api/v1/food-logs", json={
        "meal": "breakfast", "fdc_id": 123, "grams": "NaN",
    }, headers=headers).status_code == 400
    assert client.get("/api/v1/food-logs?per_page=101", headers=headers).status_code == 400
    assert client.put("/api/v1/goals/calories", json={"calories": "Infinity"}, headers=headers).status_code == 400


def test_activity_logs_require_nutrition_setup_and_respect_owner(client):
    first = register_and_login(client, "first@example.com")
    second = register_and_login(client, "second@example.com")
    payload = {
        "activity": "walking",
        "duration_minutes": 30,
        "intensity": "medium",
        "weight_kg": 75,
        "height_cm": 175,
    }
    assert client.post("/api/v1/activity-logs", json=payload, headers=first).status_code == 409
    setup = client.put("/api/v1/goals/nutrition", json={
        "age": 30, "sex": "male", "height_cm": 175,
        "weight_kg": 75, "activity_level": "moderately active", "goal": "maintain",
    }, headers=first)
    assert setup.status_code == 200
    assert setup.json["calories"] > 0
    response = client.post("/api/v1/activity-logs", json=payload, headers=first)
    assert response.status_code == 201
    assert response.json["calories_burned"] > 0
    payload["extra"] = True
    assert client.put(f"/api/v1/activity-logs/{response.json['id']}", json=payload, headers=second).status_code == 404
    assert client.put(f"/api/v1/activity-logs/{response.json['id']}", json=payload, headers=first).status_code == 200
    summary = client.get("/api/v1/reports/daily", headers=first).json
    assert summary["exercise_credit"] > 0
    assert summary["calorie_goal"] > setup.json["calories"]
    assert client.get("/api/v1/activity-logs", headers=second).json["total"] == 0
    assert client.delete(f"/api/v1/activity-logs/{response.json['id']}", headers=second).status_code == 404
    assert client.delete(f"/api/v1/activity-logs/{response.json['id']}", headers=first).status_code == 204


def _micronutrient_targets(report, *names):
    return {row["name"]: row for row in report["micronutrients"] if row["name"] in names}


def test_period_day_raises_daily_iron_and_vitamin_c_targets(client):
    headers = register_and_login(client, "period@example.com")
    setup = client.put("/api/v1/goals/nutrition", json={
        "age": 30, "sex": "female", "height_cm": 165,
        "weight_kg": 60, "activity_level": "moderately active", "goal": "maintain",
    }, headers=headers)
    assert setup.status_code == 200
    day = datetime.now(timezone.utc).date().isoformat()

    before = client.get(f"/api/v1/reports/daily?date={day}", headers=headers).json
    baseline = _micronutrient_targets(before, "Iron", "Vitamin C")
    assert baseline["Iron"]["target"] == 18
    assert baseline["Vitamin C"]["target"] == 75
    assert before["day_conditions"] == []

    logged = client.put(f"/api/v1/days/{day}/conditions", json={"conditions": ["menstruation"]},
                        headers=headers)
    assert logged.status_code == 200
    assert logged.json["conditions"] == ["menstruation"]
    assert logged.json["guidance"]

    after = client.get(f"/api/v1/reports/daily?date={day}", headers=headers).json
    raised = _micronutrient_targets(after, "Iron", "Vitamin C")
    assert raised["Iron"]["target"] == 23
    assert raised["Vitamin C"]["target"] == 110
    assert raised["Iron"]["condition_adjusted"] is True
    assert raised["Vitamin C"]["condition_adjusted"] is True
    assert after["day_conditions"] == ["menstruation"]
    assert "menstruation" in after["active_conditions"]
    assert after["condition_guidance"]

    cleared = client.delete(f"/api/v1/days/{day}/conditions", headers=headers)
    assert cleared.status_code == 200
    assert cleared.json["conditions"] == []
    restored = _micronutrient_targets(
        client.get(f"/api/v1/reports/daily?date={day}", headers=headers).json, "Iron", "Vitamin C")
    assert restored["Iron"]["target"] == 18
    assert restored["Vitamin C"]["target"] == 75


def test_period_day_rejects_male_sex_and_pregnancy_conflict(client):
    male = register_and_login(client, "male@example.com")
    assert client.put("/api/v1/goals/nutrition", json={
        "age": 30, "sex": "male", "height_cm": 175,
        "weight_kg": 75, "activity_level": "moderately active", "goal": "maintain",
    }, headers=male).status_code == 200
    day = datetime.now(timezone.utc).date().isoformat()
    assert client.put(f"/api/v1/days/{day}/conditions", json={"conditions": ["menstruation"]},
                      headers=male).status_code == 400
    assert client.put("/api/v1/settings/health", json={"conditions": ["menstruation"]},
                      headers=male).status_code == 400

    female = register_and_login(client, "pregnant@example.com")
    assert client.put("/api/v1/goals/nutrition", json={
        "age": 30, "sex": "female", "height_cm": 165,
        "weight_kg": 60, "activity_level": "moderately active", "goal": "maintain",
    }, headers=female).status_code == 200
    assert client.put("/api/v1/settings/health", json={
        "conditions": ["pregnancy"], "trimester": 2,
    }, headers=female).status_code == 200
    assert client.put(f"/api/v1/days/{day}/conditions", json={"conditions": ["menstruation"]},
                      headers=female).status_code == 400


def test_health_settings_menstruation_persists_raised_micronutrients(client):
    headers = register_and_login(client, "ongoing-period@example.com")
    assert client.put("/api/v1/goals/nutrition", json={
        "age": 30, "sex": "female", "height_cm": 165,
        "weight_kg": 60, "activity_level": "moderately active", "goal": "maintain",
    }, headers=headers).status_code == 200
    response = client.put("/api/v1/settings/health", json={"conditions": ["menstruation"]},
                          headers=headers)
    assert response.status_code == 200
    assert response.json["conditions"] == ["menstruation"]
    nutrition = client.get("/api/v1/goals/nutrition", headers=headers).json
    micros = {row["name"]: row for row in nutrition["micronutrients"]}
    assert micros["Iron"]["target"] == 23
    assert micros["Vitamin C"]["target"] == 110
    assert micros["Iron"].get("condition_adjusted") is True


def test_food_recommendations_include_vitamin_k2_and_deficiency_advice(client):
    headers = register_and_login(client, "k2@example.com")
    assert client.put("/api/v1/goals/nutrition", json={
        "age": 30, "sex": "female", "height_cm": 165,
        "weight_kg": 60, "activity_level": "moderately active", "goal": "maintain",
    }, headers=headers).status_code == 200
    catalog = client.get("/api/v1/nutrients/food-recommendations", headers=headers)
    assert catalog.status_code == 200
    assert "Vitamin K2" in catalog.json["recommendations"]
    assert catalog.json["recommendations"]["Iron"]
    day = datetime.now(timezone.utc).date().isoformat()
    report = client.get(f"/api/v1/reports/daily?date={day}", headers=headers).json
    k2 = next(row for row in report["micronutrients"] if row["name"] == "Vitamin K2")
    assert k2["target"] == 90
    assert "food_recommendations" in k2
    assert "nutrient_advice" in report
