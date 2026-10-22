import pytest
from sqlalchemy.engine import URL

import config
from main import create_app


def test_test_factory_needs_no_local_database_settings(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *_: None)
    for name in ("DATABASE_URL", "DATABASE_HOSTNAME", "DATABASE_NAME", "DATABASE_USERNAME", "DATABASE_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    app = create_app({"SECRET_KEY": "a" * 32, "JWT_SECRET_KEY": "b" * 32,
                      "SQLALCHEMY_DATABASE_URI": URL.create(
                          "postgresql+psycopg", username="test", password="test",
                          host="localhost", database="nutrition_test")})
    assert app.test_client().get("/api/v1/health").status_code == 200
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        config.database_url()


def test_heroku_database_url_uses_psycopg_and_requires_ssl(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *_: None)
    monkeypatch.setenv("DATABASE_URL", "postgres://nutrition:secret@ec2-1-2-3-4.compute.amazonaws.com:5432/nutrition")
    url = config.database_url()
    assert url.drivername == "postgresql+psycopg"
    assert url.host == "ec2-1-2-3-4.compute.amazonaws.com"
    assert url.query["sslmode"] == "require"


def test_local_database_url_does_not_require_ssl(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *_: None)
    monkeypatch.setenv("DATABASE_URL", "postgresql://nutrition:secret@localhost:5432/nutrition")
    url = config.database_url()
    assert url.drivername == "postgresql+psycopg"
    assert "sslmode" not in url.query


def test_sqlite_url_is_rejected():
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        create_app({"SECRET_KEY": "a" * 32, "JWT_SECRET_KEY": "b" * 32,
                    "SQLALCHEMY_DATABASE_URI": "sqlite://"})
