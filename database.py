from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import make_url


db = SQLAlchemy()
migrate = Migrate()


def init_database(app):
    if make_url(app.config["SQLALCHEMY_DATABASE_URI"]).get_backend_name() != "postgresql":
        raise RuntimeError("PostgreSQL is required.")
    app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {
        "pool_pre_ping": True, "connect_args": {"connect_timeout": 5},
    })
    db.init_app(app)
    migrate.init_app(app, db)


def save_calorie_target(user_id, calories):
    from models import CalorieTarget

    target = db.session.get(CalorieTarget, user_id)
    if calories is None:
        if target is not None:
            db.session.delete(target)
    elif target is None:
        db.session.add(CalorieTarget(user_id=user_id, calories=calories))
    else:
        target.calories = calories
