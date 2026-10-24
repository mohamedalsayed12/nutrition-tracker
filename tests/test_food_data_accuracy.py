"""The app's food numbers match USDA FoodData Central.

The records below are real USDA data (fetched 22 Oct 2026), written the way the
USDA API returns them: names, units such as "µg", and per-100 g amounts. Each
test runs them through the same code the app uses when you log a food.
"""
from decimal import Decimal
from types import SimpleNamespace

import pytest

from services.calc import food_measures, scaled_food_nutrients
from services.nutrient_scoring import matched_micronutrients
from services.nutrient_targets import micronutrient_targets
from services.weekly_recap import food_macros


def nutrient(name, unit, amount):
    return SimpleNamespace(name=name, unit_name=unit, amount=amount)


def portion(description, grams):
    return SimpleNamespace(portion_description=description, gram_weight=grams, amount=1, modifier=None, measure_unit=None)


def food(description, nutrients, portions=()):
    return SimpleNamespace(description=description, nutrients=[nutrient(*n) for n in nutrients],
                           food_portions=[portion(*p) for p in portions],
                           serving_size=None, serving_size_unit=None, household_serving_fulltext=None)


REFERENCE = [
    (2709215, "Apple, raw", 61, 0.17, 0.15, 14.8),
    (173944, "Bananas, raw", 89, 1.09, 0.33, 22.8),
    (2646170, "Chicken, breast, boneless, skinless, raw", 112, 22.5, 1.93, 0),
    (2707152, "Egg, whole, raw", 143, 12.4, 9.96, 0.96),
    (2705385, "Milk, whole", 61, 3.27, 3.2, 4.63),
    (2708402, "Rice, cooked, NFS", 129, 2.67, 0.28, 27.99),
    (2708489, "Oats, raw", 379, 13.15, 6.52, 67.7),
    (170379, "Broccoli, raw", 34, 2.82, 0.37, 6.64),
    (2707537, "Peanut butter", 598, 22.21, 51.36, 22.31),
    (170903, "Yogurt, Greek, plain, lowfat", 73, 9.95, 1.92, 3.94),
]


@pytest.mark.parametrize("fdc_id, description, kcal, protein, fat, carbs", REFERENCE)
@pytest.mark.parametrize("grams", [100, 150, 37.5])
def test_logged_macros_equal_usda_values_scaled_to_the_amount(fdc_id, description, kcal, protein, fat, carbs, grams):
    record = food(description, [
        ("Energy", "kJ", round(kcal * 4.184)),
        ("Energy", "kcal", kcal), ("Protein", "g", protein),
        ("Total lipid (fat)", "g", fat), ("Carbohydrate, by difference", "g", carbs),
    ])
    macros = food_macros(scaled_food_nutrients(record, Decimal(str(grams))))
    factor = grams / 100
    assert macros["Calories"] == pytest.approx(kcal * factor, abs=0.001)
    assert macros["Protein"] == pytest.approx(protein * factor, abs=0.001)
    assert macros["Fat"] == pytest.approx(fat * factor, abs=0.001)
    assert macros["Carbohydrates"] == pytest.approx(carbs * factor, abs=0.001)


@pytest.mark.parametrize("fdc_id, description, kcal, protein, fat, carbs", REFERENCE)
def test_usda_calories_agree_with_protein_carbs_and_fat(fdc_id, description, kcal, protein, fat, carbs):
    assert 4 * protein + 4 * carbs + 9 * fat == pytest.approx(kcal, rel=0.22)


def test_foundation_food_uses_the_specific_atwater_energy():
    record = food("Chicken, breast, boneless, skinless, raw", [
        ("Energy (Atwater General Factors)", "kcal", 117),
        ("Energy (Atwater Specific Factors)", "kcal", 112),
        ("Protein", "g", 22.5),
    ])
    assert food_macros(scaled_food_nutrients(record, Decimal(100)))["Calories"] == 112


APPLE = food("Apple, raw", [
    ("Energy", "kcal", 61), ("Protein", "g", 0.17), ("Total lipid (fat)", "g", 0.15),
    ("Carbohydrate, by difference", "g", 14.8), ("Fiber, total dietary", "g", 2.1),
    ("Calcium, Ca", "mg", 5), ("Iron, Fe", "mg", 0.03), ("Magnesium, Mg", "mg", 5),
    ("Phosphorus, P", "mg", 9), ("Potassium, K", "mg", 104), ("Sodium, Na", "mg", 0),
    ("Zinc, Zn", "mg", 0.02), ("Copper, Cu", "mg", 0.03), ("Selenium, Se", "µg", 0),
    ("Vitamin A, RAE", "µg", 3), ("Vitamin E (alpha-tocopherol)", "mg", 0.18),
    ("Vitamin D (D2 + D3)", "µg", 0), ("Vitamin C, total ascorbic acid", "mg", 4.6),
    ("Thiamin", "mg", 0.01), ("Riboflavin", "mg", 0.07), ("Niacin", "mg", 0.091),
    ("Vitamin B-6", "mg", 0.03), ("Vitamin B-12", "µg", 0), ("Choline, total", "mg", 3.4),
    ("Vitamin K (phylloquinone)", "µg", 2.2), ("Folate, DFE", "µg", 0),
], [("1 small", 165), ("1 medium", 200)])


def test_microgram_nutrients_are_counted():
    """USDA writes micrograms as "µg"; these used to be dropped as an unknown unit."""
    targets = micronutrient_targets(22, "male")
    eaten = matched_micronutrients(scaled_food_nutrients(APPLE, Decimal(200)), targets, "eaten")
    assert eaten["Vitamin K"] == pytest.approx(4.4)
    assert eaten["Vitamin A"] == pytest.approx(6)
    assert eaten["Vitamin D"] == 0
    assert eaten["Vitamin B12"] == 0
    assert eaten["Folate (B9)"] == 0
    assert eaten["Selenium"] == 0
    assert eaten["Vitamin C"] == pytest.approx(9.2)
    assert eaten["Potassium"] == pytest.approx(208)
    assert eaten["Iron"] == pytest.approx(0.06)
    assert {"Vitamin A", "Vitamin C", "Vitamin D", "Vitamin E", "Vitamin K", "Vitamin B6", "Vitamin B12",
            "Thiamin (B1)", "Riboflavin (B2)", "Niacin (B3)", "Folate (B9)", "Choline", "Calcium", "Iron",
            "Magnesium", "Phosphorus", "Potassium", "Sodium", "Zinc", "Copper", "Selenium"} <= set(eaten)


def test_vitamin_d_in_international_units_is_converted():
    record = food("GREEK YOGURT", [("Vitamin D (D2 + D3), International Units", "IU", 400)])
    targets = micronutrient_targets(30, "female")
    eaten = matched_micronutrients(scaled_food_nutrients(record, Decimal(100)), targets, "eaten")
    assert eaten["Vitamin D"] == pytest.approx(10)


def test_serving_weights_match_usda_portions():
    measures = {m["label"]: m["grams"] for m in food_measures(APPLE)}
    assert measures["1 medium (200 g)"] == 200
    assert measures["1 small (165 g)"] == 165


def test_milk_skips_guideline_amounts_and_defaults_to_a_cup():
    milk = food("Milk, whole", [], [
        ("Guideline amount per fl oz of beverage", 2.5), ("Quantity not specified", 244),
        ("1 individual school container", 244), ("1 cup", 244), ("Guideline amount per cup of hot cereal", 61),
    ])
    measures = food_measures(milk)
    labels = [m["label"] for m in measures]
    assert not any("Guideline" in label or "Quantity not specified" in label for label in labels)
    assert next(m for m in measures if m["default"])["label"] == "1 cup (244 g)"


def test_usda_serving_jargon_reads_as_a_serving():
    chicken = food("Chicken, breast, boneless, skinless, raw", [], [("1 RACC", 114)])
    assert food_measures(chicken)[0]["label"] == "1 serving (114 g)"
