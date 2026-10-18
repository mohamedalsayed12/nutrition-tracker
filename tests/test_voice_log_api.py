from types import SimpleNamespace


PROFILE = {
    "age": 30, "sex": "female", "height_cm": 165, "weight_kg": 60,
    "activity_level": "moderately active",
}


def auth_headers(client, email="voice@example.com"):
    assert client.post("/api/v1/users", json={
        "name": "Voice User", "email": email, "password": "a-secure-password", **PROFILE,
    }).status_code == 201
    token = client.post("/api/v1/auth/login", json={
        "email": email, "password": "a-secure-password",
    }).json["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_from_voice_logs_best_usda_match(client, monkeypatch):
    headers = auth_headers(client)
    assert client.put("/api/v1/goals/goal", headers=headers, json={"goal": "maintain"}).status_code == 200

    monkeypatch.setenv("FDC_API_KEY", "test-key")
    monkeypatch.setattr(
        "services.voice_log.search_foods",
        lambda query: [{"fdc_id": 171077, "description": "Chicken, breast, grilled", "data_type": "SR Legacy",
                        "brand_name": None, "gtin_upc": None}],
    )
    food = SimpleNamespace(
        description="Chicken, breast, grilled",
        nutrients=[SimpleNamespace(name="Energy", unit_name="kcal", amount=165)],
    )
    monkeypatch.setattr("services.logs.get_food_client", lambda: SimpleNamespace(get_food=lambda _: food))

    response = client.post("/api/v1/food-logs/from-voice", headers=headers, json={
        "transcript": "180 grams of chicken breast for dinner",
        "auto_log": True,
    })
    assert response.status_code == 201, response.json
    body = response.json
    assert body["meal"] == "dinner"
    assert body["grams"] == 180.0
    assert body["logged"]["fdc_id"] == 171077
    assert body["logged"]["meal"] == "dinner"
    assert body["logged"]["grams"] == 180.0
