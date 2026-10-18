from datetime import datetime, timezone


def register_female(client, email="period@example.com"):
    assert client.post("/api/v1/users", json={
        "name": "Period User", "email": email, "password": "a-secure-password",
    }).status_code == 201
    token = client.post("/api/v1/auth/login", json={
        "email": email, "password": "a-secure-password",
    }).json["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    setup = client.put("/api/v1/goals/nutrition", headers=headers, json={
        "age": 28, "sex": "female", "height_cm": 165, "weight_kg": 60,
        "activity_level": "moderately active", "goal": "maintain",
    })
    assert setup.status_code == 200
    return headers


def test_logging_period_raises_iron_and_vitamin_c_on_daily_report(client):
    headers = register_female(client)
    day = datetime.now(timezone.utc).date().isoformat()
    before = client.get(f"/api/v1/reports/daily?date={day}", headers=headers).json
    iron_before = next(row for row in before["micronutrients"] if row["name"] == "Iron")
    vitamin_c_before = next(row for row in before["micronutrients"] if row["name"] == "Vitamin C")

    response = client.put(f"/api/v1/days/{day}/conditions", headers=headers, json={
        "conditions": ["menstruation"],
    })
    assert response.status_code == 200
    assert response.json["conditions"] == ["menstruation"]
    assert response.json["guidance"]

    after = client.get(f"/api/v1/reports/daily?date={day}", headers=headers).json
    iron_after = next(row for row in after["micronutrients"] if row["name"] == "Iron")
    vitamin_c_after = next(row for row in after["micronutrients"] if row["name"] == "Vitamin C")
    assert after["day_conditions"] == ["menstruation"]
    assert "menstruation" in after["active_conditions"]
    assert iron_after["target"] == iron_before["target"] + 5
    assert vitamin_c_after["target"] == vitamin_c_before["target"] + 35
    assert iron_after["condition_adjusted"] is True
    assert any(row["name"] == "Vitamin K2" for row in after["micronutrients"])
    assert "food_recommendations" in iron_after
    assert "nutrient_advice" in after

    assert client.delete(f"/api/v1/days/{day}/conditions", headers=headers).status_code == 200
    cleared = client.get(f"/api/v1/days/{day}/conditions", headers=headers).json
    assert cleared["conditions"] == []


def test_period_logging_rejects_male_nutrition_sex(client):
    assert client.post("/api/v1/users", json={
        "name": "Male User", "email": "male@example.com", "password": "a-secure-password",
    }).status_code == 201
    token = client.post("/api/v1/auth/login", json={
        "email": "male@example.com", "password": "a-secure-password",
    }).json["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.put("/api/v1/goals/nutrition", headers=headers, json={
        "age": 30, "sex": "male", "height_cm": 175, "weight_kg": 75,
        "activity_level": "moderately active", "goal": "maintain",
    }).status_code == 200
    day = datetime.now(timezone.utc).date().isoformat()
    response = client.put(f"/api/v1/days/{day}/conditions", headers=headers, json={
        "conditions": ["menstruation"],
    })
    assert response.status_code == 400


def test_food_recommendations_endpoint(client):
    headers = register_female(client, email="foods@example.com")
    response = client.get("/api/v1/nutrients/food-recommendations", headers=headers)
    assert response.status_code == 200
    recommendations = response.json["recommendations"]
    assert "Vitamin K2" in recommendations
    assert "Iron" in recommendations
    assert recommendations["Vitamin K2"]
