import pytest

from services.calc import (
    UserInfo,
    calculate_goal_targets,
    mifflin_st_jeor_bmr,
    protein_per_kg,
    protein_targets,
)


def info(age=22, sex="male", height=180, weight=80, activity="moderately active"):
    person = UserInfo()
    person.func(age=age, gender=sex, height=height, weight=weight, activity_level=activity)
    return person


def test_bmr_uses_mifflin_st_jeor_for_each_sex():
    assert mifflin_st_jeor_bmr(80, 180, 22, "male") == 1820.0
    assert mifflin_st_jeor_bmr(80, 180, 22, "female") == 1654.0
    with pytest.raises(ValueError):
        mifflin_st_jeor_bmr(80, 180, 22, "other")


def test_calories_change_with_each_of_sex_height_weight_and_age():
    base = calculate_goal_targets(info(), "maintain", False)[2]
    assert base == round(1820 * 1.55, 1)
    assert calculate_goal_targets(info(sex="female"), "maintain", False)[2] < base
    assert calculate_goal_targets(info(height=170), "maintain", False)[2] < base
    assert calculate_goal_targets(info(weight=70), "maintain", False)[2] < base
    assert calculate_goal_targets(info(age=50), "maintain", False)[2] < base


def test_protein_minimum_follows_body_weight_age_and_goal():
    assert protein_per_kg(30) == 0.8
    assert protein_per_kg(18) == 0.85
    assert protein_per_kg(70) == 1.0
    assert protein_per_kg(30, "lose_weight") == 1.2
    assert protein_per_kg(30, "gain_weight") == 1.6
    assert protein_targets(2500, 80, 30)[0] == 64.0
    assert protein_targets(2500, 60, 30)[0] == 48.0
    assert protein_targets(3000, 80, 30, "gain_weight")[0] == 128.0


def test_protein_maximum_is_35_percent_of_calories_and_never_below_the_minimum():
    assert protein_targets(2000, 70, 30) == (56.0, 175.0)
    assert protein_targets(1200, 150, 30, "gain_weight") == (240.0, 240.0)


def test_goal_targets_use_weight_based_protein():
    _, _, calories, protein_min, protein_max, _ = calculate_goal_targets(info(), "gain_weight", False)
    assert protein_min == 128.0
    assert protein_max == round(calories * 0.35 / 4, 1)
