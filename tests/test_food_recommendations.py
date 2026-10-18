from types import SimpleNamespace
import unittest

from services.food_recommendations import (
    all_nutrient_food_recommendations,
    deficiency_advice,
    foods_for_nutrient,
    is_deficient,
)
from services.nutrient_scoring import _target_name, remaining_targets
from services.nutrient_targets import micronutrient_targets


class FoodRecommendationTest(unittest.TestCase):
    def test_every_tracked_nutrient_has_food_suggestions(self):
        recommendations = all_nutrient_food_recommendations()
        for row in micronutrient_targets(30, "female"):
            self.assertIn(row["name"], recommendations)
            self.assertGreaterEqual(len(recommendations[row["name"]]), 2)
            self.assertTrue(all("food" in item and "reason" in item
                                for item in recommendations[row["name"]]))

    def test_vitamin_k2_has_target_and_foods(self):
        targets = {row["name"]: row for row in micronutrient_targets(30, "female")}
        self.assertEqual(targets["Vitamin K2"]["target"], 90)
        self.assertEqual(targets["Vitamin K2"]["unit"], "mcg")
        foods = foods_for_nutrient("Vitamin K2")
        self.assertTrue(any("Natto" in item["food"] for item in foods))

    def test_menaquinone_labels_map_to_vitamin_k2(self):
        self.assertEqual(_target_name("Vitamin K (Menaquinone-4)"), "Vitamin K2")
        self.assertEqual(_target_name("Menaquinone-7"), "Vitamin K2")
        self.assertEqual(_target_name("Vitamin K (phylloquinone)"), "Vitamin K")

    def test_deficient_intake_gets_food_advice(self):
        targets = [row for row in micronutrient_targets(30, "female")
                   if row["name"] in ("Iron", "Vitamin K2", "Sodium")]
        logs = [SimpleNamespace(nutrients=[
            {"name": "Iron, Fe", "unit": "MG", "eaten": 4},
            {"name": "Vitamin K (Menaquinone-4)", "unit": "UG", "eaten": 10},
            {"name": "Sodium, Na", "unit": "MG", "eaten": 4000},
        ])]
        rows = {row["name"]: row for row in remaining_targets(logs, targets)}
        self.assertTrue(rows["Iron"]["deficient"])
        self.assertIn("Lentils", rows["Iron"]["advice"] or "")
        self.assertTrue(rows["Vitamin K2"]["deficient"])
        self.assertTrue(any(item["food"].startswith("Natto")
                            for item in rows["Vitamin K2"]["food_recommendations"]))
        self.assertTrue(rows["Sodium"]["deficient"])
        self.assertIn("lower-sodium", rows["Sodium"]["advice"])
        advice = deficiency_advice(list(rows.values()))
        self.assertEqual({row["name"] for row in advice}, {"Iron", "Vitamin K2", "Sodium"})

    def test_meeting_target_is_not_deficient(self):
        row = {"name": "Iron", "percent": 100, "limit": False}
        self.assertFalse(is_deficient(row))
        row = {"name": "Sodium", "percent": 90, "limit": True}
        self.assertFalse(is_deficient(row))


if __name__ == "__main__":
    unittest.main()
