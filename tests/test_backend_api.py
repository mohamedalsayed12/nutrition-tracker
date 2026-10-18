from types import SimpleNamespace
from datetime import datetime, timezone

def register_and_login(client, email):
    registration = client.post("/api/v1/users", json={
        "name": "Test User", "email": email, "password": "a-secure-password",
    })
    assert registration.status_code == 201
    login = client.post("/api/v1/auth/login", json={
        "email": email, "password": "a-secure-password",
    })
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json['access_token']}"}


def test_auth_and_private_profile(client):
    assert client.get("/api/v1/users/me").status_code == 401
    first = register_and_login(client, "first@example.com")
    assert client.get("/api/v1/users/me", headers=first).json["email"] == "first@example.com"
    assert client.post("/api/v1/users", json={
        "name": "Other", "email": "first@example.com", "password": "a-secure-password",
    }).status_code == 409
    assert client.post("/api/v1/auth/login", json={
        "email": "first@example.com", "password": "wrong-password",
    }).status_code == 401


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
        "activity": "Walk outdoors", "activity_type": "walking",
        "duration_minutes": 30, "weight_kg": 75, "height_cm": 175,
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
