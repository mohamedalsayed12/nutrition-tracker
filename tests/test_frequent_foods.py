from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from services.calc import frequent_food_choices


def food_log(meal, fdc_id, name, grams, when):
    return SimpleNamespace(meal=meal, fdc_id=fdc_id, food_name=name,
                           grams=grams, logged_at=when)


class FrequentFoodTest(unittest.TestCase):
    def test_frequent_foods_by_meal(self):
        now = datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
        logs = [
            food_log("breakfast", 1, "Egg, whole", 120, now),
            food_log("breakfast", 1, "Egg, whole", 120, now - timedelta(seconds=1)),
            food_log("breakfast", 2, "Oatmeal", 80, now - timedelta(hours=1)),
            food_log("breakfast", 1, "Egg, whole", 100, now - timedelta(days=1)),
            food_log("lunch", 2, "Oatmeal", 200, now - timedelta(days=2)),
        ]
        choices = frequent_food_choices(logs)
        self.assertEqual([food["fdc_id"] for food in choices["breakfast"]], [1, 2])
        self.assertEqual(choices["breakfast"][0]["count"], 2)
        self.assertEqual(choices["breakfast"][0]["grams"], 120)
        self.assertEqual(choices["lunch"][0]["grams"], 200)
        self.assertEqual(choices["dinner"], [])


if __name__ == "__main__":
    unittest.main()
