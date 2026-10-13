
from imports import json, os, sqlite3, time, SQLAlchemy, OperationalError, g


db = SQLAlchemy()
SEARCH_CACHE_PATH = os.path.join(os.path.dirname(__file__), "food_cache.sqlite3")
FOOD_INDEX_PATH = os.path.join(os.path.dirname(__file__), "instance", "food_index.sqlite3")


def configure_database(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
    db.init_app(app)
    app.teardown_appcontext(close_search_cache)
    with app.app_context():
        db.create_all()
        with db.engine.begin() as connection:
            columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(health_preferences)")}
            for column in ("custom_protein", "custom_fat"):
                if column not in columns:
                    try:
                        connection.exec_driver_sql(f"ALTER TABLE health_preferences ADD COLUMN {column} FLOAT")
                    except OperationalError as exc:
                        if "duplicate column name" not in str(exc).lower():
                            raise


def search_cache_connection():
    connection = getattr(g, "_database", None)
    if connection is None:
        connection = g._database = sqlite3.connect(SEARCH_CACHE_PATH)
    return connection


def close_search_cache(_exception=None):
    connection = getattr(g, "_database", None)
    if connection is not None:
        connection.close()
    index_connection = getattr(g, "_food_index", None)
    if index_connection is not None:
        index_connection.close()


def food_index_connection():
    if not os.path.isfile(FOOD_INDEX_PATH):
        return None
    connection = getattr(g, "_food_index", None)
    if connection is None:
        connection = sqlite3.connect(f"file:{FOOD_INDEX_PATH}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        g._food_index = connection
    return connection


def indexed_food_search(words, fdc_id=None, barcode=None):
    connection = food_index_connection()
    if connection is None:
        return None
    if fdc_id is not None:
        rows = connection.execute(
            "SELECT fdc_id, description, data_type, brand_name, gtin_upc, publication_date "
            "FROM foods WHERE fdc_id = ?", (fdc_id,)
        ).fetchall()
    elif barcode is not None:
        rows = connection.execute(
            "SELECT fdc_id, description, data_type, brand_name, gtin_upc, publication_date "
            "FROM foods WHERE gtin_upc = ? OR ltrim(gtin_upc, '0') = ? "
            "ORDER BY publication_date DESC LIMIT 100",
            (barcode, barcode.lstrip("0")),
        ).fetchall()
    else:
        if not words:
            return []
        expression = " AND ".join(f'"{word}"*' for word in words)
        rows = []
        for branded in (0, 1):
            rows.extend(connection.execute(
                "SELECT foods.fdc_id, foods.description, foods.data_type, "
                "foods.brand_name, foods.gtin_upc, foods.publication_date FROM food_search "
                "JOIN foods ON foods.fdc_id = food_search.rowid "
                "WHERE food_search MATCH ? AND (foods.data_type = 'Branded') = ? "
                "ORDER BY bm25(food_search) LIMIT 150",
                (expression, branded),
            ).fetchall())
    return [dict(row) for row in rows]


def user_food_search_counts(user_id):
    from models import FoodLog
    return dict(
        db.session.query(FoodLog.fdc_id, db.func.count(FoodLog.id))
        .filter(FoodLog.user_id == user_id)
        .group_by(FoodLog.fdc_id).all()
    )


def cached_food_search(query):
    connection = search_cache_connection()
    connection.execute(
        "CREATE TABLE IF NOT EXISTS food_search_cache "
        "(query TEXT PRIMARY KEY, results TEXT NOT NULL, fetched_at INTEGER NOT NULL)"
    )
    row = connection.execute(
        "SELECT results FROM food_search_cache WHERE query = ? AND fetched_at > ?",
        (f"{query}|foods:v3", int(time.time()) - 86400),
    ).fetchone()
    return json.loads(row[0]) if row is not None else None


def save_food_search(query, foods):
    connection = search_cache_connection()
    connection.execute(
        "INSERT OR REPLACE INTO food_search_cache (query, results, fetched_at) "
        "VALUES (?, ?, ?)", (f"{query}|foods:v3", json.dumps(foods), int(time.time()))
    )
    connection.commit()


def save_exercise_search(query, exercises):
    connection = search_cache_connection()
    connection.execute(
        "CREATE TABLE IF NOT EXISTS exercise_search_cache "
        "(query TEXT PRIMARY KEY, results TEXT NOT NULL, fetched_at INTEGER NOT NULL)"
    )
    connection.execute(
        "INSERT OR REPLACE INTO exercise_search_cache (query, results, fetched_at) "
        "VALUES (?, ?, ?)", (query, json.dumps(exercises), int(time.time()))
    )
    connection.commit()


def get_record(model, key):
    return db.session.get(model, key)


def add_record(record):
    db.session.add(record)


def delete_record(record):
    db.session.delete(record)


def commit_changes():
    db.session.commit()


def rollback_changes():
    db.session.rollback()


def user_by_email(email):
    from models import User
    return User.query.filter_by(email=email).first()


def user_food_logs(user_id, newest_first=False):
    from models import FoodLog
    query = FoodLog.query.filter_by(user_id=user_id)
    if newest_first:
        query = query.order_by(FoodLog.logged_at.desc(), FoodLog.id.desc())
    return query.all()


def user_activity_logs(user_id):
    from models import ActivityLog
    return (ActivityLog.query.filter_by(user_id=user_id)
            .order_by(ActivityLog.logged_at.desc()).all())


def saved_days_count(user_id, first_day, last_day):
    from models import SavedEatingDay
    return (SavedEatingDay.query.filter_by(user_id=user_id)
            .filter(SavedEatingDay.day >= first_day, SavedEatingDay.day <= last_day).count())


def matching_food_logs(user_id, meal, fdc_id, grams):
    from models import FoodLog
    return (FoodLog.query.filter_by(user_id=user_id, meal=meal, fdc_id=fdc_id, grams=grams)
            .order_by(FoodLog.logged_at.desc(), FoodLog.id.desc()).all())


def save_calorie_target(user_id, calories):
    from models import CalorieTarget
    target = get_record(CalorieTarget, user_id)
    if calories is None:
        if target is not None:
            delete_record(target)
    elif target is None:
        add_record(CalorieTarget(user_id=user_id, calories=calories))
    else:
        target.calories = calories


def reopen_eating_days(user_id, days):
    from models import SavedEatingDay
    for day in days:
        saved = get_record(SavedEatingDay, (user_id, day))
        if saved is not None:
            delete_record(saved)
