from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from services.calc import frequent_food_choices
from services.food_search import popular_logged_foods


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

    def test_popular_logged_foods_ranks_by_count(self):
        now = datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
        logs = [
            food_log("breakfast", 1, "Egg, whole", 120, now),
            food_log("lunch", 1, "Egg, whole", 100, now - timedelta(hours=2)),
            food_log("dinner", 1, "Egg, whole", 110, now - timedelta(days=1)),
            food_log("breakfast", 2, "Oatmeal", 80, now - timedelta(hours=1)),
            food_log("lunch", 3, "Rice", 150, now - timedelta(days=2)),
        ]

        class Query:
            def filter_by(self, **kwargs):
                return self

            def order_by(self, *args):
                return self

            def all(self):
                return logs

        class Session:
            def query(self, *args):
                return Query()

        with patch("services.food_search.db") as fake_db:
            fake_db.session = Session()
            popular = popular_logged_foods(1, limit=5)
        self.assertEqual(popular[0]["fdc_id"], 1)
        self.assertEqual(popular[0]["count"], 3)
        self.assertEqual(popular[0]["meals"][0]["meal"], "breakfast")


if __name__ == "__main__":
    unittest.main()
