"""Per-meal iron absorption check.

Iron from plant foods (non-heme iron: beans, lentils, spinach, fortified cereals)
is absorbed much better when vitamin C is eaten in the same meal. A daily vitamin C
total cannot show this, because vitamin C at breakfast does nothing for iron eaten
at dinner. So this module looks at each meal on its own.

Source: NIH Office of Dietary Supplements, Iron fact sheet
https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/

USDA data does not say how much of a food's iron is heme (from meat and fish,
which absorbs well on its own) or non-heme, so the check works on total iron and
the tip explains that vitamin C matters most for iron from plant foods.
"""

from services.nutrient_scoring import _convert, _target_name

MEALS = ("breakfast", "lunch", "dinner", "snack")

# A meal with at least this much iron is worth checking. Smaller amounts make
# little difference to the day either way.
IRON_WORTH_CHECKING_MG = 2.0

# About the vitamin C in half an orange or a few slices of red pepper. Studies of
# non-heme iron absorption show a clear increase from roughly this amount upwards.
VITAMIN_C_HELPFUL_MG = 25.0

# The tips only show for health settings that raise iron needs: periods (iron lost
# each month) and pregnancy (27 mg/day). Everyone else's iron target is easily met
# without planning meals around it, so the tips would just be noise.
IRON_CONDITIONS = {"menstruation", "pregnancy"}

VITAMIN_C_IDEAS = "red or yellow pepper, an orange, kiwi, strawberries, tomato or broccoli"


def _meal_amount(food_logs, nutrient_name):
    """Total mg of one nutrient across the given logs, and whether any log reported it."""
    total = 0.0
    reported = False
    for log in food_logs:
        for nutrient in log.nutrients or ():
            if _target_name(nutrient.get("name", "")) != nutrient_name:
                continue
            amount = _convert(nutrient.get("eaten"), nutrient.get("unit"), "mg")
            if amount is not None:
                total += amount
                reported = True
                break
    return total, reported


def iron_absorption_checks(food_logs, conditions=()):
    """One entry per meal that has a meaningful amount of iron.

    Only for users whose health settings include periods or pregnancy; for
    everyone else this returns an empty list. status is "add_vitamin_c" when the
    meal has iron but little vitamin C, or "good" when it already pairs the two.
    """
    if not IRON_CONDITIONS & set(conditions or ()):
        return []
    highlight = True
    checks = []
    for meal in MEALS:
        logs = [log for log in food_logs if log.meal == meal]
        if not logs:
            continue
        iron, iron_reported = _meal_amount(logs, "Iron")
        if not iron_reported or iron < IRON_WORTH_CHECKING_MG:
            continue
        vitamin_c, vitamin_c_reported = _meal_amount(logs, "Vitamin C")
        if vitamin_c >= VITAMIN_C_HELPFUL_MG:
            status = "good"
            tip = (f"This {meal} pairs its iron with vitamin C, which helps your body "
                   "absorb iron from plant foods.")
        else:
            status = "add_vitamin_c"
            tip = (f"This {meal} has {iron:.1f} mg of iron but little vitamin C. Adding some "
                   f"({VITAMIN_C_IDEAS}) helps your body absorb iron from plant foods.")
        checks.append({
            "meal": meal,
            "iron_mg": round(iron, 1),
            "vitamin_c_mg": round(vitamin_c, 1) if vitamin_c_reported else None,
            "status": status,
            "tip": tip,
            "highlight": highlight,
        })
    return checks
