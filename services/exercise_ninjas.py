"""API Ninjas exercise search and calories-burned estimates."""

from __future__ import annotations

import os

import requests
from flask import abort

from services.calc import EXERCISE_METS, estimate_exercise_calories


INTENSITY_TO_ACTIVITY_TYPE = {
    "easy": "other_light",
    "medium": "other_moderate",
    "hard": "other_vigorous",
}

# Applied when API Ninjas returns a single match (no intensity ladder to pick from).
INTENSITY_MULTIPLIER = {
    "easy": 0.85,
    "medium": 1.0,
    "hard": 1.2,
}

FALLBACK_ACTIVITIES = [
    "walking",
    "running",
    "cycling",
    "swimming",
    "yoga",
    "weight lifting",
    "elliptical",
    "rowing",
    "hiking",
    "jump rope",
    "aerobics",
    "dancing",
]


def _api_key():
    return (os.getenv("API_NINJAS_KEY") or "").strip()


def kg_to_lb(weight_kg):
    return max(50.0, min(500.0, float(weight_kg) * 2.2046226218))


def cm_to_inches(height_cm):
    return max(36.0, min(96.0, float(height_cm) / 2.54))


def pick_intensity_match(results, intensity):
    """Choose one caloriesburned match for easy / medium / hard.

    When several intensity variants are returned, pick by burn rate.
    When only one match exists, scale total calories by intensity.
    """
    if not results:
        raise ValueError("No matching exercise found.")
    ranked = sorted(results, key=lambda item: float(item.get("calories_per_hour") or 0))
    if len(ranked) == 1:
        chosen = dict(ranked[0])
        factor = INTENSITY_MULTIPLIER[intensity]
        chosen["total_calories"] = round(float(chosen["total_calories"]) * factor, 1)
        chosen["calories_per_hour"] = round(float(chosen["calories_per_hour"]) * factor, 1)
        chosen["intensity"] = intensity
        chosen["intensity_scaled"] = factor != 1.0
        return chosen

    index = {"easy": 0, "medium": len(ranked) // 2, "hard": len(ranked) - 1}[intensity]
    chosen = dict(ranked[index])
    chosen["intensity"] = intensity
    chosen["intensity_scaled"] = False
    return chosen


def _ninjas_caloriesburned(activity, duration_minutes, weight_kg, age=None, sex=None, height_cm=None):
    api_key = _api_key()
    if not api_key:
        return None
    params = {
        "activity": activity,
        "weight": round(kg_to_lb(weight_kg), 1),
        "duration": max(1, int(round(float(duration_minutes)))),
    }
    if age is not None and sex in ("male", "female") and height_cm is not None:
        params.update(age=int(age), sex=sex, height=round(cm_to_inches(height_cm), 1))
    response = requests.get(
        "https://api.api-ninjas.com/v1/caloriesburned",
        params=params,
        headers={"X-Api-Key": api_key},
        timeout=8,
    )
    if response.status_code == 400:
        raise ValueError(response.json().get("error") if response.content else "Invalid exercise request.")
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("Unexpected calories burned response.")
    return payload


def search_exercise_options(query, duration_minutes=30, weight_kg=70):
    """Search API Ninjas caloriesburned activities for a single-selection list."""
    query = (query or "").strip()
    if len(query) < 2:
        return []
    if len(query) > 80:
        abort(400, description="Search is too long.")

    try:
        results = _ninjas_caloriesburned(query, duration_minutes, weight_kg)
    except ValueError as error:
        abort(400, description=str(error))
    except requests.RequestException:
        abort(502, description="Exercise search is temporarily unavailable.")

    if results is None:
        # No API key: offer local fallbacks that match the query.
        needle = query.lower()
        matches = [name for name in FALLBACK_ACTIVITIES if needle in name]
        if not matches:
            matches = [query]
        return [
            {
                "name": name,
                "calories_per_hour": None,
                "duration_minutes": float(duration_minutes),
                "total_calories": None,
                "source": "fallback",
            }
            for name in matches[:10]
        ]

    return [
        {
            "name": item.get("name"),
            "calories_per_hour": item.get("calories_per_hour"),
            "duration_minutes": item.get("duration_minutes", duration_minutes),
            "total_calories": item.get("total_calories"),
            "source": "api_ninjas",
        }
        for item in results
        if item.get("name")
    ][:10]


def estimate_ninjas_calories(activity, duration_minutes, weight_kg, intensity,
                             age=None, sex=None, height_cm=None):
    """Return calories burned for one exercise at one intensity."""
    if intensity not in INTENSITY_TO_ACTIVITY_TYPE:
        raise ValueError("Choose easy, medium, or hard intensity.")
    activity_type = INTENSITY_TO_ACTIVITY_TYPE[intensity]
    met = EXERCISE_METS[activity_type][0]

    try:
        results = _ninjas_caloriesburned(activity, duration_minutes, weight_kg, age, sex, height_cm)
    except requests.RequestException as error:
        raise ValueError("Exercise calorie lookup is temporarily unavailable.") from error

    if results is None:
        if age is None or sex is None or height_cm is None:
            raise ValueError("Complete nutrition setup before logging exercise.")
        burned = estimate_exercise_calories(
            duration_minutes, activity_type, weight_kg, height_cm, age, sex)
        burned = round(burned * INTENSITY_MULTIPLIER[intensity] / INTENSITY_MULTIPLIER["medium"], 1)
        return {
            "activity": activity,
            "matched_name": activity,
            "calories_burned": burned,
            "calories_per_hour": round(burned * 60 / max(duration_minutes, 1), 1),
            "duration_minutes": float(duration_minutes),
            "intensity": intensity,
            "activity_type": activity_type,
            "met": met,
            "source": "fallback_met",
        }

    chosen = pick_intensity_match(results, intensity)
    return {
        "activity": activity,
        "matched_name": chosen["name"],
        "calories_burned": round(float(chosen["total_calories"]), 1),
        "calories_per_hour": round(float(chosen["calories_per_hour"]), 1),
        "duration_minutes": float(chosen.get("duration_minutes") or duration_minutes),
        "intensity": intensity,
        "activity_type": activity_type,
        "met": met,
        "source": "api_ninjas",
        "intensity_scaled": bool(chosen.get("intensity_scaled")),
    }
