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
        SimpleNamespace(fdc_id=104, description="Egg substitute, liquid", brand_name=None,
                        data_type="SR Legacy", gtin_upc=None),
    ]

    class FoodClient:
        def get_food(self, fdc_id):
            return next(food for food in foods if food.fdc_id == fdc_id)

        def search(self, query, page_size, data_type=None, **kwargs):
            items = foods
            if data_type:
                wanted = set(data_type)
                items = [food for food in foods if food.data_type in wanted]
            return SimpleNamespace(foods=items)

    monkeypatch.setenv("FDC_API_KEY", "test-key")
    monkeypatch.setattr(food_search, "get_food_client", FoodClient)

    for query, expected in (("egg", 101), ("soup car", 102),
                            ("morning oats", 103), ("123456789012", 103),
                            ("fdc:102", 102)):
        response = client.get("/api/v1/foods", query_string={"q": query})
        assert response.status_code == 200
        assert expected in [food["fdc_id"] for food in response.json["foods"]]

    egg = client.get("/api/v1/foods", query_string={"q": "egg"}).json["foods"]
    assert egg[0]["fdc_id"] == 101
    assert egg[0]["previously_logged"] is False
    assert "log_count" in egg[0]


def test_food_search_boosts_previously_logged_foods(client, monkeypatch, authorized_headers):
    foods = [
        SimpleNamespace(fdc_id=201, description="Chicken breast, grilled", brand_name=None,
                        data_type="Foundation", gtin_upc=None),
        SimpleNamespace(fdc_id=202, description="Chicken soup", brand_name=None,
                        data_type="Survey (FNDDS)", gtin_upc=None),
    ]

    class FoodClient:
        def get_food(self, fdc_id):
            return next(food for food in foods if food.fdc_id == fdc_id)

        def search(self, query, page_size, data_type=None, **kwargs):
            items = foods
            if data_type:
                wanted = set(data_type)
                items = [food for food in foods if food.data_type in wanted]
            return SimpleNamespace(foods=items)

    monkeypatch.setenv("FDC_API_KEY", "test-key")
    monkeypatch.setattr(food_search, "get_food_client", FoodClient)
    monkeypatch.setattr(food_search, "_user_food_counts", lambda user_id: {202: 8, 201: 1})

    response = client.get("/api/v1/foods", query_string={"q": "chicken"}, headers=authorized_headers)
    assert response.status_code == 200
    results = response.json["foods"]
    assert results[0]["fdc_id"] == 202
    assert results[0]["log_count"] == 8
    assert results[0]["previously_logged"] is True


def test_food_search_requires_usda_key(client, monkeypatch):
    monkeypatch.delenv("FDC_API_KEY", raising=False)
    response = client.get("/api/v1/foods", query_string={"q": "egg"})
    assert response.status_code == 503
