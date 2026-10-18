import unittest

from services.voice_parse import parse_voice_log


class VoiceParseTest(unittest.TestCase):
    def test_grams_and_meal(self):
        parsed = parse_voice_log("I ate 180 grams of chicken breast for dinner")
        self.assertEqual(parsed["meal"], "dinner")
        self.assertEqual(parsed["grams"], 180.0)
        self.assertIn("chicken", parsed["food_query"])
        self.assertIn("breast", parsed["food_query"])

    def test_ounces_convert_to_grams(self):
        parsed = parse_voice_log("six ounces of salmon for lunch")
        self.assertEqual(parsed["meal"], "lunch")
        self.assertAlmostEqual(parsed["grams"], 170.1, places=0)
        self.assertIn("salmon", parsed["food_query"])

    def test_counted_eggs_default_weight(self):
        parsed = parse_voice_log("two eggs for breakfast")
        self.assertEqual(parsed["meal"], "breakfast")
        self.assertEqual(parsed["grams"], 100.0)
        self.assertIn("egg", parsed["food_query"])

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            parse_voice_log("   ")


if __name__ == "__main__":
    unittest.main()
