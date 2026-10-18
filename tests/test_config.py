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


def test_sqlite_url_is_rejected():
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        create_app({"SECRET_KEY": "a" * 32, "JWT_SECRET_KEY": "b" * 32,
                    "SQLALCHEMY_DATABASE_URI": "sqlite://"})
