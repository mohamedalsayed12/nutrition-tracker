
import json
import math
import os
import re
import secrets
import sqlite3
import time
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import unquote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import flask
import requests
from dotenv import load_dotenv
from flask import Blueprint, Flask, g
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from healthsciencecalculator.get_bmr import get_bmr
from healthsciencecalculator.get_tdee import get_tdee
from sqlalchemy.exc import IntegrityError, OperationalError
from usda_fdc import FdcClient
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired
from importlib import import_module


_PROJECT_EXPORTS = {
    "bcrypt": "extensions", "login_manager": "extensions",
    "configure_database": "db", "cached_food_search": "db",
    "save_food_search": "db", "save_exercise_search": "db",
    "get_record": "db", "add_record": "db", "delete_record": "db",
    "commit_changes": "db", "rollback_changes": "db",
    "user_food_logs": "db", "user_activity_logs": "db",
    "saved_days_count": "db", "matching_food_logs": "db",
    "save_calorie_target": "db", "reopen_eating_days": "db",
    "auth_bp": "auth",
    "api_bp": "api", "get_food_client": "api",
    "CalorieTarget": "models", "NutritionTargets": "models",
    "UserMeasurements": "models", "UserActivityBaseline": "models",
    "MacroSplit": "models", "HealthPreferences": "models",
    "MealSubmission": "models", "FoodLog": "models",
    "SavedEatingDay": "models", "ActivityLog": "models",
    "ExerciseDetails": "models", "ExerciseTargetCredit": "models",
    "npc_rating": "nutrient_scoring",
    "nutrient_per_100_calories": "nutrient_scoring",
    "remaining_targets": "nutrient_scoring",
    "micronutrient_targets": "nutrient_targets",
    "condition_micronutrient_guidance": "nutrient_targets",
    "build_weekly_recap": "weekly_recap", "food_macros": "weekly_recap",
    "UserInfo": "calc", "calculate_goal_targets": "calc",
    "configured_micronutrients": "calc", "apply_health_preferences": "calc",
    "fat_target_range": "calc", "custom_macro_targets": "calc",
    "EXERCISE_METS": "calc", "estimate_exercise_calories": "calc",
    "active_exercise_calories": "calc", "scaled_food_nutrients": "calc",
    "grams_for_measure": "calc",
    "exercise_adjusted_target": "calc", "daily_target_progress": "calc",
    "weekly_target_labels": "calc",
    "frequent_food_choices": "calc",
    "validate_care_plan_macros": "calc", "condition_nutrition_data": "calc",
}


def __getattr__(name):
    module_name = _PROJECT_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
