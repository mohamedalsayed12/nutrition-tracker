import unittest
from unittest.mock import patch

from services.exercise_ninjas import (
    INTENSITY_MULTIPLIER,
    estimate_ninjas_calories,
    pick_intensity_match,
    search_exercise_options,
)


SAMPLE = [
    {"name": "Running, 5 mph", "calories_per_hour": 500, "duration_minutes": 30, "total_calories": 250},
    {"name": "Running, 6 mph", "calories_per_hour": 650, "duration_minutes": 30, "total_calories": 325},
    {"name": "Running, 8 mph", "calories_per_hour": 900, "duration_minutes": 30, "total_calories": 450},
]


class ExerciseNinjasTest(unittest.TestCase):
    def test_pick_intensity_from_ladder(self):
        easy = pick_intensity_match(SAMPLE, "easy")
        medium = pick_intensity_match(SAMPLE, "medium")
        hard = pick_intensity_match(SAMPLE, "hard")
        self.assertEqual(easy["name"], "Running, 5 mph")
        self.assertEqual(medium["name"], "Running, 6 mph")
        self.assertEqual(hard["name"], "Running, 8 mph")
        self.assertFalse(easy["intensity_scaled"])

    def test_single_match_scales_by_intensity(self):
        single = [SAMPLE[1]]
        easy = pick_intensity_match(single, "easy")
        hard = pick_intensity_match(single, "hard")
        self.assertEqual(easy["total_calories"], round(325 * INTENSITY_MULTIPLIER["easy"], 1))
        self.assertEqual(hard["total_calories"], round(325 * INTENSITY_MULTIPLIER["hard"], 1))
        self.assertTrue(easy["intensity_scaled"])

    def test_estimate_uses_api_ninjas_when_key_present(self):
        with patch.dict("os.environ", {"API_NINJAS_KEY": "test-key"}), \
             patch("services.exercise_ninjas.requests.get") as get:
            get.return_value.status_code = 200
            get.return_value.content = b"[]"
            get.return_value.json.return_value = SAMPLE
            get.return_value.raise_for_status = lambda: None
            result = estimate_ninjas_calories(
                activity="running",
                duration_minutes=30,
                weight_kg=75,
                intensity="hard",
                age=30,
                sex="male",
                height_cm=175,
            )
        self.assertEqual(result["source"], "api_ninjas")
        self.assertEqual(result["matched_name"], "Running, 8 mph")
        self.assertEqual(result["calories_burned"], 450)
        self.assertEqual(result["intensity"], "hard")
        self.assertEqual(result["activity_type"], "other_vigorous")

    def test_estimate_falls_back_without_api_key(self):
        with patch.dict("os.environ", {"API_NINJAS_KEY": ""}, clear=False):
            result = estimate_ninjas_calories(
                activity="walking",
                duration_minutes=30,
                weight_kg=75,
                intensity="easy",
                age=30,
                sex="female",
                height_cm=165,
            )
        self.assertEqual(result["source"], "fallback_met")
        self.assertGreater(result["calories_burned"], 0)
        self.assertEqual(result["activity_type"], "other_light")

    def test_search_fallback_without_api_key(self):
        with patch.dict("os.environ", {"API_NINJAS_KEY": ""}, clear=False):
            results = search_exercise_options("run")
        self.assertTrue(any(item["name"] == "running" for item in results))
        self.assertEqual(results[0]["source"], "fallback")


if __name__ == "__main__":
    unittest.main()
