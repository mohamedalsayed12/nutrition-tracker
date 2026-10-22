from types import SimpleNamespace
import unittest

from services.calc import (condition_nutrition_data, custom_macro_targets,
                  daily_target_progress, validate_care_plan_macros,
                  configured_micronutrients)
from services.nutrient_targets import condition_micronutrient_guidance, micronutrient_targets
from services.nutrient_scoring import remaining_targets


class ConditionTargetTest(unittest.TestCase):
    def test_periods_raise_iron_only_and_personal_overrides_win(self):
        preferences = SimpleNamespace(conditions=["menstruation", "ibs", "diabetes"],
                                      micronutrient_overrides={})
        # Vitamin C stays at the usual female reference (65 mg at 14-18, 75 mg for adults).
        for age, iron, vitamin_c in ((16, 15, 65), (30, 18, 75), (55, 18, 75)):
            targets = {row["name"]: row["target"] for row in configured_micronutrients(age, "female", preferences)}
            self.assertEqual(targets["Iron"], iron)
            self.assertEqual(targets["Vitamin C"], vitamin_c)
        plain = {row["name"]: row["target"] for row in micronutrient_targets(30, "female")}
        self.assertEqual(plain["Iron"], 18)
        self.assertEqual(plain["Vitamin C"], 75)
        preferences.micronutrient_overrides = {"Iron": 20}
        targets = configured_micronutrients(30, "female", preferences)
        iron = next(row for row in targets if row["name"] == "Iron")
        self.assertEqual(iron["target"], 20)
        self.assertTrue(iron["custom"])

    def test_pregnancy_targets_and_override_survive_multiple_profiles(self):
        preferences = SimpleNamespace(conditions=["pregnancy", "ibs", "diabetes"],
                                      micronutrient_overrides={"Iron": 30})
        targets = {row["name"]: row["target"] for row in configured_micronutrients(30, "female", preferences)}
        self.assertEqual(targets["Iron"], 30)
        self.assertEqual(targets["Folate (B9)"], 600)
        self.assertNotIn("Iodine", targets)
        self.assertEqual(targets["Choline"], 450)

    def test_each_profile_focus_matches_tracked_nutrients_and_overlaps(self):
        profiles = condition_micronutrient_guidance(["pregnancy", "diabetes", "ibs", "menstruation"])
        names = {row["name"] for row in micronutrient_targets(30, "female")}
        self.assertEqual(len(profiles), 4)
        for profile in profiles:
            self.assertTrue(profile["nutrients"])
            self.assertTrue(set(profile["nutrients"]).issubset(names))
        overlapping = condition_micronutrient_guidance(["menstruation", "ibs", "menstruation"])
        self.assertEqual(sum("Iron" in profile["nutrients"] for profile in overlapping), 2)
        self.assertEqual(condition_micronutrient_guidance(None), [])

    def test_focus_progress_preserves_missing_data_and_uses_personal_target(self):
        preferences = SimpleNamespace(conditions=["menstruation"], micronutrient_overrides={"Iron": 20})
        targets = configured_micronutrients(30, "female", preferences)
        logs = [SimpleNamespace(nutrients=[{"name": "Iron, Fe", "unit": "MG", "eaten": 5}]),
                SimpleNamespace(nutrients=[])]
        rows = {row["name"]: row for row in remaining_targets(logs, targets)}
        self.assertEqual(rows["Iron"]["percent"], 25)
        self.assertTrue(rows["Iron"]["partial"])
        self.assertIsNone(rows["Vitamin C"]["logged"])
        self.assertIsNone(rows["Vitamin C"]["percent"])

    def test_personal_macros_fill_remaining_calories(self):
        split = SimpleNamespace(carbs_percent=50, protein_percent=30, fat_percent=20)
        preferences = SimpleNamespace(custom_carbs=150, custom_protein=None, custom_fat=None)
        targets = custom_macro_targets(2000, split, preferences)
        self.assertEqual(targets["carbs"], 150)
        self.assertEqual(targets["protein"], 210)
        self.assertEqual(targets["fat"], 62.2)
        self.assertTrue(targets["carbs_overridden"])
        self.assertFalse(targets["protein_overridden"])

    def test_reject_macros_above_calories(self):
        preferences = SimpleNamespace(custom_carbs=300, custom_protein=200, custom_fat=100)
        with self.assertRaisesRegex(ValueError, "exceed"):
            validate_care_plan_macros(2000, preferences)

    def test_personal_protein_fat_and_fiber_progress(self):
        preferences = SimpleNamespace(custom_carbs=None, custom_protein=100,
                                      custom_fat=70, conditions=["diabetes", "ibs"])
        nutrition = SimpleNamespace(age=30, protein_min=50, protein_max=175, carbs=275)
        logs = [SimpleNamespace(nutrients=[
            {"name": "Fiber, total dietary", "unit": "G", "eaten": 8.0},
            {"name": "Protein", "unit": "G", "eaten": 30.0},
        ])]
        progress, *_ = daily_target_progress(logs, 2000, 0, nutrition, None, preferences)
        labels = {row["name"]: row["target_label"] for row in progress}
        self.assertEqual(labels["Protein"], "100 g")
        self.assertEqual(labels["Fat"], "70 g")
        fiber = condition_nutrition_data(logs, 2000)
        self.assertEqual(fiber["fiber_logged"], 8)
        self.assertEqual(fiber["fiber_goal"], 28)
        self.assertAlmostEqual(fiber["fiber_percent"], 28.6)

if __name__ == "__main__":
    unittest.main()
