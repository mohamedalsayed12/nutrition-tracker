import unittest

from services.nutrient_scoring import (
    food_nutrient_density,
    macro_density,
    nutrient_per_100_calories,
    npc_rating,
)
from services.nutrient_targets import micronutrient_targets


SPINACH = [
    {"name": "Energy", "unit": "kcal", "per_100g": 23},
    {"name": "Protein", "unit": "g", "per_100g": 2.9},
    {"name": "Carbohydrate, by difference", "unit": "g", "per_100g": 3.6},
    {"name": "Total lipid (fat)", "unit": "g", "per_100g": 0.4},
    {"name": "Iron, Fe", "unit": "mg", "per_100g": 2.7},
    {"name": "Vitamin C, total ascorbic acid", "unit": "mg", "per_100g": 28.1},
    {"name": "Calcium, Ca", "unit": "mg", "per_100g": 99},
]


class NutrientDensityTest(unittest.TestCase):
    def test_nutrient_per_100_calories(self):
        self.assertAlmostEqual(nutrient_per_100_calories(18, 200), 9)
        with self.assertRaises(ValueError):
            nutrient_per_100_calories(1, 0)

    def test_macro_density_scales_to_100_kcal(self):
        density = macro_density(SPINACH)
        self.assertEqual(density["energy_kcal_per_100g"], 23)
        # 2.9 g protein / 23 kcal * 100 ≈ 12.61 g per 100 kcal
        self.assertAlmostEqual(density["per_100kcal"]["protein"], 2.9 / 23 * 100, places=2)

    def test_npc_rating_scores_dense_produce_highly(self):
        targets = micronutrient_targets(30, "female")
        rating = npc_rating(SPINACH, targets, daily_calories=2000)
        self.assertIsNotNone(rating["score"])
        self.assertGreater(rating["score"], 0)
        iron = next(row for row in rating["nutrients"] if row["name"] == "Iron")
        self.assertAlmostEqual(iron["per_100kcal"], 2.7 / 23 * 100, places=2)
        # Iron RDA 18 mg; spinach ~11.7 mg / 100 kcal → ~65% of target per 100 kcal
        self.assertGreater(iron["percent_of_target_per_100kcal"], 50)
        self.assertTrue(any("per 100 kcal" in reason for reason in rating["reasons"]))

    def test_food_nutrient_density_combines_macros_and_micros(self):
        targets = micronutrient_targets(30, "female")
        result = food_nutrient_density(SPINACH, targets=targets, daily_calories=2000)
        self.assertIn("score", result)
        self.assertIn("protein", result["macros_per_100kcal"])
        self.assertTrue(any(row["name"] == "Iron" for row in result["micronutrients"]))
        self.assertTrue(result["reasons"])

    def test_missing_targets_still_returns_macros(self):
        result = food_nutrient_density(SPINACH)
        self.assertIsNone(result["score"])
        self.assertEqual(result["macros_per_100kcal"]["protein"], round(2.9 / 23 * 100, 2))
        self.assertEqual(result["micronutrients"], [])


if __name__ == "__main__":
    unittest.main()
