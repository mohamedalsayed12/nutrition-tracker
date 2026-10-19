from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from usda_fdc import FdcResourceNotFoundError

from database import db
from models import FoodLog, SavedEatingDay
from services import food_search


BAHRAIN = ZoneInfo("Asia/Bahrain")  # UTC+3, no daylight saving


def _user_id(client, headers):
    return client.get("/api/v1/users/me", headers=headers).json["id"]


def _add_food(app, user_id, logged_at, fdc_id=123):
    with app.app_context():
        log = FoodLog(user_id=user_id, meal="snack", fdc_id=fdc_id, food_name="Dates",
                      grams=50, nutrients=[], logged_at=logged_at)
        db.session.add(log)
        db.session.commit()
        return log.id


# --- Saving a day uses the same timezone as the daily report ---------------

def test_save_day_uses_users_timezone(app, client, authorized_headers):
    user_id = _user_id(client, authorized_headers)
    # 01:00 on 20 October in Bahrain is 22:00 on 19 October in UTC.
    _add_food(app, user_id, datetime(2026, 10, 20, 1, 0, tzinfo=BAHRAIN))

    report = client.get("/api/v1/reports/daily", headers=authorized_headers,
                        query_string={"date": "2026-10-20", "timezone": "Asia/Bahrain"}).json
    assert report["food_log_count"] == 1

    saved = client.put("/api/v1/days/2026-10-20/save", headers=authorized_headers,
                       query_string={"timezone": "Asia/Bahrain"})
    assert saved.status_code == 200
    assert saved.json["timezone"] == "Asia/Bahrain"

    # In UTC that food belongs to the 19th, so the 20th has nothing to save.
    utc = client.put("/api/v1/days/2026-10-20/save", headers=authorized_headers)
    assert utc.status_code == 409


def test_deleting_food_unsaves_the_local_day(app, client, authorized_headers):
    user_id = _user_id(client, authorized_headers)
    log_id = _add_food(app, user_id, datetime(2026, 10, 20, 1, 0, tzinfo=BAHRAIN))
    client.put("/api/v1/days/2026-10-20/save", headers=authorized_headers,
               query_string={"timezone": "Asia/Bahrain"})
    assert client.get("/api/v1/days", headers=authorized_headers).json["days"] == ["2026-10-20"]

    assert client.delete(f"/api/v1/food-logs/{log_id}", headers=authorized_headers).status_code == 204
    assert client.get("/api/v1/days", headers=authorized_headers).json["days"] == []


def test_deleting_food_keeps_other_saved_days(app, client, authorized_headers):
    user_id = _user_id(client, authorized_headers)
    _add_food(app, user_id, datetime(2026, 10, 19, 12, 0, tzinfo=BAHRAIN))
    other = _add_food(app, user_id, datetime(2026, 10, 20, 12, 0, tzinfo=BAHRAIN))
    client.put("/api/v1/days/2026-10-19/save", headers=authorized_headers,
               query_string={"timezone": "Asia/Bahrain"})

    client.delete(f"/api/v1/food-logs/{other}", headers=authorized_headers)
    assert client.get("/api/v1/days", headers=authorized_headers).json["days"] == ["2026-10-19"]


def test_save_day_rejects_bad_input(client, authorized_headers):
    bad_date = client.put("/api/v1/days/not-a-date/save", headers=authorized_headers)
    assert bad_date.status_code == 400
    bad_zone = client.put("/api/v1/days/2026-10-20/save", headers=authorized_headers,
                          query_string={"timezone": "Mars/Base"})
    assert bad_zone.status_code == 400


# --- Timestamps keep the same instant whatever the database timezone is -----

def test_timestamps_do_not_shift_with_database_timezone(app, client, authorized_headers):
    user_id = _user_id(client, authorized_headers)
    instant = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    with app.app_context():
        db.session.execute(text("SET TIME ZONE 'Asia/Bahrain'"))
        db.session.add(FoodLog(user_id=user_id, meal="lunch", fdc_id=1, food_name="Rice",
                               grams=100, nutrients=[], logged_at=instant))
        db.session.commit()
        stored = db.session.query(FoodLog).filter_by(user_id=user_id).one().logged_at
        assert stored.tzinfo is not None
        assert stored == instant

    item = client.get("/api/v1/food-logs", headers=authorized_headers).json["items"][0]
    assert item["logged_at"] == "2026-10-19T12:00:00+00:00"


def test_saved_day_records_its_timezone(app, client, authorized_headers):
    user_id = _user_id(client, authorized_headers)
    _add_food(app, user_id, datetime.now(timezone.utc) - timedelta(minutes=1))
    today = datetime.now(timezone.utc).date().isoformat()
    client.put(f"/api/v1/days/{today}/save", headers=authorized_headers)
    with app.app_context():
        assert db.session.query(SavedEatingDay).one().timezone == "UTC"


# --- Food search puts foods you have logged before first ---------------------

def _search_client(monkeypatch):
    foods = [SimpleNamespace(fdc_id=fdc_id, description=f"Apple {fdc_id}", brand_name=None,
                             data_type="Foundation", gtin_upc=None) for fdc_id in (1, 2, 3)]
    monkeypatch.setenv("FDC_API_KEY", "test-key")
    monkeypatch.setattr(food_search, "get_food_client", lambda: SimpleNamespace(
        search=lambda query, page_size: SimpleNamespace(foods=foods)))


def test_search_puts_previously_logged_foods_first(app, client, authorized_headers, monkeypatch):
    _search_client(monkeypatch)
    _add_food(app, _user_id(client, authorized_headers), datetime.now(timezone.utc), fdc_id=3)

    signed_in = client.get("/api/v1/foods", headers=authorized_headers,
                           query_string={"q": "apple"}).json["foods"]
    assert [food["fdc_id"] for food in signed_in] == [3, 1, 2]
    assert [food["previously_logged"] for food in signed_in] == [True, False, False]

    anonymous = client.get("/api/v1/foods", query_string={"q": "apple"}).json["foods"]
    assert [food["fdc_id"] for food in anonymous] == [1, 2, 3]
    assert not any(food["previously_logged"] for food in anonymous)


def test_search_does_not_use_other_users_history(app, client, authorized_headers, monkeypatch):
    _search_client(monkeypatch)
    other = client.post("/api/v1/users", json={
        "name": "Other", "email": "other@example.com", "password": "a-secure-password"}).json["id"]
    _add_food(app, other, datetime.now(timezone.utc), fdc_id=3)
    results = client.get("/api/v1/foods", headers=authorized_headers,
                         query_string={"q": "apple"}).json["foods"]
    assert [food["fdc_id"] for food in results] == [1, 2, 3]


# --- Error statuses ------------------------------------------------------------

def test_measures_for_unknown_food_returns_404(client, monkeypatch):
    def missing(_fdc_id):
        raise FdcResourceNotFoundError("not found", 404)

    monkeypatch.setattr("routers.foods.get_food_client",
                        lambda: SimpleNamespace(get_food=missing))
    response = client.get("/api/v1/foods/999999/measures")
    assert response.status_code == 404
    assert response.json == {"error": "USDA food not found."}


def test_ready_returns_503_when_database_is_down(client, monkeypatch):
    def down(*_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    monkeypatch.setattr(db.session, "execute", down)
    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json["status"] == "unavailable"
