from types import SimpleNamespace

from services import food_search


def test_food_search_uses_usda_client(client, monkeypatch):
    foods = [
        SimpleNamespace(fdc_id=101, description="Egg, raw", brand_name=None,
                        data_type="Foundation", gtin_upc=None),
        SimpleNamespace(fdc_id=102, description="Carrot soup", brand_name=None,
                        data_type="Survey (FNDDS)", gtin_upc=None),
        SimpleNamespace(fdc_id=103, description="Oat cereal", brand_name="Morning Oats",
                        data_type="Branded", gtin_upc="00123456789012"),
    ]

    class FoodClient:
        def get_food(self, fdc_id):
            return next(food for food in foods if food.fdc_id == fdc_id)

        def search(self, query, page_size):
            return SimpleNamespace(foods=foods)

    monkeypatch.setenv("FDC_API_KEY", "test-key")
    monkeypatch.setattr(food_search, "get_food_client", FoodClient)

    for query, expected in (("egg", 101), ("soup car", 102),
                            ("morning oats", 103), ("123456789012", 103),
                            ("fdc:102", 102)):
        response = client.get("/api/v1/foods", query_string={"q": query})
        assert response.status_code == 200
        assert expected in [food["fdc_id"] for food in response.json["foods"]]


def test_food_search_requires_usda_key(client, monkeypatch):
    monkeypatch.delenv("FDC_API_KEY", raising=False)
    response = client.get("/api/v1/foods", query_string={"q": "egg"})
    assert response.status_code == 503
