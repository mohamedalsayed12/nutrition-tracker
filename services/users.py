from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from database import db
from models import CalorieTarget, OnboardingProfile, User, UserActivityBaseline, UserMeasurements
from schemas import NutritionSetup
from services.goals import set_nutrition_goals
from utils import hash_password


def profile_payload(profile):
    if profile is None:
        return None
    return dict(
        age=profile.age,
        sex=profile.sex,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        activity_level=profile.activity_level,
        goal=profile.goal,
    )


def user_payload(user):
    profile = db.session.get(OnboardingProfile, user.uid)
    nutrition_configured = db.session.get(CalorieTarget, user.uid) is not None
    return dict(
        id=user.uid,
        name=user.username,
        email=user.email,
        profile=profile_payload(profile),
        needs_goal=profile is not None and not nutrition_configured,
        nutrition_configured=nutrition_configured,
    )


def create_user(data):
    user = User(username=data.name, email=str(data.email), password=hash_password(data.password))
    db.session.add(user)
    try:
        db.session.flush()
        profile = OnboardingProfile(
            user_id=user.uid,
            age=data.age,
            sex=data.sex,
            height_cm=data.height_cm,
            weight_kg=data.weight_kg,
            activity_level=data.activity_level,
        )
        db.session.add(profile)
        measurements = UserMeasurements(
            user_id=user.uid, height_cm=data.height_cm, weight_kg=data.weight_kg,
        )
        db.session.add(measurements)
        baseline = UserActivityBaseline(user_id=user.uid, activity_level=data.activity_level)
        db.session.add(baseline)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise
    return user_payload(user)


def set_goal_from_profile(user_id, goal):
    profile = db.session.get(OnboardingProfile, user_id)
    if profile is None:
        raise ValueError("Complete registration profile details before choosing a goal.")
    setup = NutritionSetup(
        age=profile.age,
        sex=profile.sex,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        activity_level=profile.activity_level,
        goal=goal,
    )
    result = set_nutrition_goals(user_id, setup)
    profile = db.session.get(OnboardingProfile, user_id)
    profile.goal = goal
    profile.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return dict(**result, goal=goal, profile=profile_payload(profile))
