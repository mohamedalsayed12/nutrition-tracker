from functools import wraps
from typing import Annotated, Literal

from flask import request
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator, model_validator


PositiveAmount = Annotated[float, Field(gt=0, le=10000, allow_inf_nan=False)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


ActivityLevel = Literal["sedentary", "lightly active", "moderately active", "very active", "extra active"]
Sex = Literal["male", "female"]
Goal = Literal["maintain", "lose_weight", "gain_weight"]


class UserCreate(InputModel):
    name: Name
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    age: int = Field(ge=18, le=100, strict=True)
    sex: Sex
    height_cm: float = Field(ge=50, le=300)
    weight_kg: float = Field(ge=20, le=500)
    activity_level: ActivityLevel

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return str(value).lower()

    @field_validator("password")
    @classmethod
    def limit_password_bytes(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes.")
        return value


class UserLogin(InputModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class GoalChoice(InputModel):
    goal: Goal


class FoodLogCreate(InputModel):
    meal: Literal["breakfast", "lunch", "dinner", "snack"]
    fdc_id: int = Field(gt=0, strict=True)
    grams: PositiveAmount


class ActivityLogCreate(InputModel):
    activity: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    activity_type: Literal["walking", "running", "cycling", "swimming", "strength", "yoga", "other_light", "other_moderate", "other_vigorous"]
    duration_minutes: float = Field(gt=0, le=1440)
    weight_kg: float = Field(ge=10, le=500)
    height_cm: float = Field(ge=50, le=300)
    extra: bool = Field(default=False, strict=True)


class CalorieGoal(InputModel):
    calories: float = Field(ge=500, le=10000)


class NutritionSetup(InputModel):
    age: int = Field(ge=18, le=100, strict=True)
    sex: Sex
    height_cm: float = Field(ge=50, le=300)
    weight_kg: float = Field(ge=20, le=500)
    activity_level: ActivityLevel
    goal: Goal


class MacroSplitInput(InputModel):
    carbs_percent: float = Field(ge=0, le=100)
    protein_percent: float = Field(ge=0, le=100)
    fat_percent: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def total_is_100(self):
        if abs(self.carbs_percent + self.protein_percent + self.fat_percent - 100) > 0.0001:
            raise ValueError("Macro percentages must total 100.")
        return self


DAY_SCOPED_CONDITIONS = Literal["menstruation"]
HEALTH_CONDITIONS = Literal["pregnancy", "diabetes", "ibs", "menstruation"]


class HealthSettings(InputModel):
    conditions: list[HEALTH_CONDITIONS] = Field(default_factory=list)
    trimester: Literal[1, 2, 3] | None = None
    custom_calories: float | None = Field(default=None, ge=500, le=10000)
    custom_carbs: float | None = Field(default=None, gt=0, le=1500)
    custom_protein: float | None = Field(default=None, gt=0, le=1500)
    custom_fat: float | None = Field(default=None, gt=0, le=1500)
    micronutrient_overrides: dict[str, Annotated[float, Field(gt=0, le=1000000)]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_conditions(self):
        if {"pregnancy", "menstruation"}.issubset(self.conditions):
            raise ValueError("Pregnancy and menstruation cannot both be selected.")
        if "pregnancy" in self.conditions and self.trimester is None:
            raise ValueError("Choose a pregnancy trimester.")
        return self


class DayConditions(InputModel):
    """Log conditions that adjust nutrient targets for a single day.

    Currently supports menstruation (period days). Chronic conditions such as
    pregnancy, diabetes, and IBS belong in health settings.
    """

    conditions: list[DAY_SCOPED_CONDITIONS] = Field(default_factory=list)


class Pagination(InputModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


def validate_body(schema):
    def decorate(function):
        @wraps(function)
        def validated(*args, **kwargs):
            data = schema.model_validate(request.get_json(silent=True))
            return function(*args, data=data, **kwargs)
        validated.request_schema = schema
        return validated
    return decorate
