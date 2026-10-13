
import csv
import io
import os
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import build_food_index
import db
from app import app


def csv_bytes(fields, records):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records)
    return buffer.getvalue().encode("utf-8")


class FoodIndexTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        archive_path = f"{self.directory.name}/foods.zip"
        self.index_path = f"{self.directory.name}/index.sqlite3"
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("release/food.csv", csv_bytes(
                ["fdc_id", "data_type", "description", "publication_date"],
                [
                    {"fdc_id": 101, "data_type": "foundation_food", "description": "Egg, raw"},
                    {"fdc_id": 102, "data_type": "survey_fndds_food",
                     "description": "Carrot soup"},
                    {"fdc_id": 103, "data_type": "branded_food", "description": "Oat cereal"},
                    {"fdc_id": 104, "data_type": "foundation_food",
                     "description": "Eggplant, raw"},
                ],
            ))
            archive.writestr("release/branded_food.csv", csv_bytes(
                ["fdc_id", "brand_owner", "brand_name", "gtin_upc"],
                [{"fdc_id": 103, "brand_owner": "Oat Company",
                  "brand_name": "Morning Oats", "gtin_upc": "00123456789012"}],
            ))
        build_food_index.build_index(archive_path, self.index_path)
        previous_path = db.FOOD_INDEX_PATH
        db.FOOD_INDEX_PATH = self.index_path
        self.addCleanup(setattr, db, "FOOD_INDEX_PATH", previous_path)

    def test_name_fragments_brand_and_barcode(self):
        with app.test_client() as client:
            for query, expected in (("egg", 101), ("soup car", 102),
                                    ("morning oats", 103), ("123456789012", 103),
                                    ("fdc:102", 102)):
                with self.subTest(query=query):
                    response = client.get("/api/foods", query_string={"q": query})
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(expected, [food["fdc_id"]
                                             for food in response.json["foods"]])

    def test_whole_word_ranking_uses_local_index(self):
        with patch.dict(os.environ, {"FDC_API_KEY": ""}):
            with app.test_client() as client:
                response = client.get("/api/foods", query_string={"q": "egg"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["foods"][0]["fdc_id"], 101)


if __name__ == "__main__":
    unittest.main()
