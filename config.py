import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url


ROOT = Path(__file__).resolve().parent


def database_url():
    value = os.getenv("DATABASE_URL")
    if value:
        url = make_url(value)
        if url.drivername in {"postgres", "postgresql"}:
            url = url.set(drivername="postgresql+psycopg")
        if url.get_backend_name() != "postgresql":
            raise RuntimeError("PostgreSQL is required.")
        return url
    fields = ("DATABASE_HOSTNAME", "DATABASE_NAME", "DATABASE_USERNAME", "DATABASE_PASSWORD")
    if any(os.getenv(field) for field in fields):
        if not all(os.getenv(field) for field in fields):
            raise RuntimeError("Set all database settings or use DATABASE_URL.")
        return URL.create(
            "postgresql+psycopg", username=os.environ["DATABASE_USERNAME"],
            password=os.environ["DATABASE_PASSWORD"], host=os.environ["DATABASE_HOSTNAME"],
            port=int(os.getenv("DATABASE_PORT", "5432")), database=os.environ["DATABASE_NAME"],
        )
    raise RuntimeError("Set DATABASE_URL or the PostgreSQL database settings.")


def load_config(overrides=None):
    load_dotenv(ROOT / ".env")
    return {
        "SECRET_KEY": os.getenv("SECRET_KEY"),
        "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY"),
        "JWT_ACCESS_TOKEN_EXPIRES": timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))),
        "SQLALCHEMY_DATABASE_URI": (overrides or {}).get("SQLALCHEMY_DATABASE_URI") or database_url(),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "FRONTEND_ORIGINS": [origin.strip() for origin in os.getenv("FRONTEND_ORIGIN", "").split(",") if origin.strip()],
        "MAX_CONTENT_LENGTH": 1024 * 1024,
    }
