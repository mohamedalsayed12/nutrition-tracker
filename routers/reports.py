from datetime import date, datetime, timedelta

from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import jwt_required

from database import db
from models import FoodLog, SavedEatingDay
from oauth2 import current_user_id
from services.reports import daily_report, day_range, frequent_foods, report_timezone, weekly_report


router = Blueprint("reports", __name__)


def requested_day(zone, name="date"):
    raw = request.args.get(name)
    try:
        return date.fromisoformat(raw) if raw else datetime.now(zone).date()
    except ValueError:
        raise ValueError("Use an ISO date: YYYY-MM-DD.") from None


@router.get("/reports/daily")
@jwt_required()
def daily():
    zone = report_timezone(request.args.get("timezone", "UTC"))
    return jsonify(daily_report(current_user_id(), requested_day(zone), zone))


@router.get("/reports/weekly")
@jwt_required()
def weekly():
    zone = report_timezone(request.args.get("timezone", "UTC"))
    week_start = requested_day(zone, "week_start")
    if "week_start" not in request.args:
        week_start -= timedelta(days=week_start.weekday())
    return jsonify(weekly_report(current_user_id(), week_start, zone))


@router.get("/foods/frequent")
@jwt_required()
def frequent():
    return jsonify(foods=frequent_foods(current_user_id()))


@router.put("/days/<day>/save")
@jwt_required()
def save_day(day):
    try:
        day = date.fromisoformat(day)
    except ValueError:
        raise ValueError("Use an ISO date: YYYY-MM-DD.") from None
    # Use the same timezone as the daily report, so a saved day covers
    # exactly the food that report showed.
    zone = report_timezone(request.args.get("timezone", "UTC"))
    start, end = day_range(day, zone)
    user_id = current_user_id()
    if not db.session.query(FoodLog.id).filter(FoodLog.user_id == user_id, FoodLog.logged_at >= start, FoodLog.logged_at < end).first():
        abort(409, description="Log food before saving a day.")
    saved = db.session.get(SavedEatingDay, (user_id, day))
    if saved is None:
        db.session.add(SavedEatingDay(user_id=user_id, day=day, timezone=str(zone)))
    else:
        saved.timezone = str(zone)
    db.session.commit()
    return jsonify(date=day.isoformat(), timezone=str(zone), saved=True)


@router.get("/days")
@jwt_required()
def saved_days():
    days = db.session.query(SavedEatingDay).filter_by(user_id=current_user_id()).order_by(SavedEatingDay.day.desc()).limit(366).all()
    return jsonify(days=[day.day.isoformat() for day in days])
