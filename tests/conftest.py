import os

import pytest
from sqlalchemy.engine import make_url

from config import load_config
from database import db
from main import create_app


@pytest.fixture
def app():
    application_url = make_url(load_config()["SQLALCHEMY_DATABASE_URI"])
    test_url = make_url(os.environ["TEST_DATABASE_URL"]) if os.getenv("TEST_DATABASE_URL") else (
        application_url.set(database=os.getenv("TEST_DATABASE_NAME", "nutrition_test"))
    )
    if (test_url.get_backend_name() != "postgresql"
            or not (test_url.database or "").endswith("_test")
            or test_url == application_url):
        raise RuntimeError("Tests require a separate PostgreSQL database ending in _test.")
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-session-secret-with-32-chars-minimum",
        "JWT_SECRET_KEY": "test-jwt-secret-with-32-chars-minimum",
        "SQLALCHEMY_DATABASE_URI": test_url,
        "FRONTEND_ORIGINS": ["http://localhost:3000"],
    })
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def authorized_headers(client):
    response = client.post("/api/v1/users", json={
        "name": "Test User", "email": "user@example.com", "password": "a-secure-password",
        "age": 30, "sex": "male", "height_cm": 175, "weight_kg": 75,
        "activity_level": "moderately active",
    })
    assert response.status_code == 201
    response = client.post("/api/v1/auth/login", json={
        "email": "user@example.com", "password": "a-secure-password",
    })
    return {"Authorization": f"Bearer {response.json['access_token']}"}
