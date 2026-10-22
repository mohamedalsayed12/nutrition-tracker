from datetime import datetime, timezone

import pytest

from database import db
from models import User


def setup_nutrition(client, headers):
    response = client.put("/api/v1/goals/nutrition", headers=headers, json={
        "age": 30, "sex": "male", "height_cm": 175, "weight_kg": 75,
        "activity_level": "moderately active", "goal": "maintain",
    })
    assert response.status_code == 200


def _csrf(page):
    import re
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.decode())
    if match is None:
        match = re.search(r'value="([^"]+)"[^>]*name="csrf_token"', page.decode())
    assert match, page.decode()
    return match.group(1)


def test_browser_pages_are_available(client):
    login = client.get("/login")
    assert login.status_code == 200
    assert b"Login" in login.data
    register = client.get("/register")
    assert register.status_code == 200
    assert b"REGISTER NOW" in register.data
    homepage = client.get("/homepage")
    assert homepage.status_code == 302
    assert "/login" in homepage.headers["Location"]
    missing = client.get("/static/example.css")
    assert missing.status_code == 404
    assert missing.is_json

    created = client.post("/register", data={
        "csrf_token": _csrf(register.data), "name": "Page User",
        "email": "page@example.com", "password": "a-secure-password",
    })
    assert created.status_code == 302
    signed_in = client.post("/login", data={
        "csrf_token": _csrf(client.get("/login").data),
        "email": "page@example.com", "password": "a-secure-password",
    }, follow_redirects=True)
    assert b"Meals Log" in signed_in.data
    assert client.get("/UserInfo").status_code == 200
    assert client.get("/weekly-recap").status_code == 200


@pytest.mark.parametrize("payload", [
    {"name": "A", "email": "bad@", "password": "a-secure-password"},
    {"name": "A", "email": "user@example.com", "password": "short"},
    {"name": "A", "email": "user@example.com", "password": "a-secure-password", "uid": 99},
    [],
])
def test_user_schema_rejects_invalid_input(client, payload):
    response = client.post("/api/v1/users", json=payload)
    assert response.status_code == 400
    assert response.is_json


def test_deleted_user_token_cannot_access_resources(client, app, authorized_headers):
    with app.app_context():
        db.session.query(User).delete()
        db.session.commit()
    assert client.get("/api/v1/food-logs", headers=authorized_headers).status_code == 401


def test_health_settings_macros_and_reports(client, authorized_headers):
    headers = authorized_headers
    setup_nutrition(client, headers)
    assert client.put("/api/v1/settings/macro-split", headers=headers, json={
        "carbs_percent": 40, "protein_percent": 30, "fat_percent": 30,
    }).status_code == 200
    assert client.put("/api/v1/settings/macro-split", headers=headers, json={
        "carbs_percent": 40, "protein_percent": 40, "fat_percent": 40,
    }).status_code == 400
    response = client.put("/api/v1/settings/health", headers=headers, json={
        "conditions": ["diabetes"], "custom_calories": 2000, "custom_protein": 100,
    })
    assert response.status_code == 200
    assert response.json["custom_protein"] == 100
    response = client.put("/api/v1/settings/health", headers=headers, json={
        "conditions": ["diabetes"], "custom_calories": 500, "custom_protein": 1500,
    })
    assert response.status_code == 400
    assert client.get("/api/v1/settings/health", headers=headers).json["custom_calories"] == 2000
    response = client.get("/api/v1/reports/daily?timezone=Europe/London", headers=headers)
    assert response.status_code == 200
    assert response.json["calorie_goal"] == 2000
    weekly = client.get("/api/v1/reports/weekly", headers=headers)
    assert weekly.status_code == 200
    assert datetime.fromisoformat(weekly.json["week_start"]).weekday() == 0
    assert client.get("/api/v1/reports/daily?timezone=invalid", headers=headers).status_code == 400


def test_json_api_spec_and_cors(client):
    specification = client.get("/openapi.json")
    assert specification.status_code == 200
    paths = specification.json["paths"]
    assert paths["/api/v1/users"]["post"]["requestBody"]["content"]["application/json"]["schema"]["properties"]["email"]
    assert paths["/api/v1/food-logs/{log_id}"]["delete"]["security"] == [{"bearerAuth": []}]
    response = client.options("/api/v1/users", headers={
        "Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST",
    })
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"


def test_sql_input_cannot_bypass_login_or_change_query_structure(client, authorized_headers):
    response = client.post("/api/v1/auth/login", json={
        "email": "user@example.com", "password": "' OR '1'='1",
    })
    assert response.status_code == 401
    response = client.post("/api/v1/food-logs", headers=authorized_headers, json={
        "meal": "breakfast", "fdc_id": "1; DROP TABLE users", "grams": 50,
    })
    assert response.status_code == 400
    response = client.get("/api/v1/users/me", headers=authorized_headers)
    assert response.status_code == 200
    assert response.json["email"] == "user@example.com"
