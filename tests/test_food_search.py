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

        def search(self, query, page_size, data_type=None):
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


def test_filtered_usda_search_is_sent_as_post(monkeypatch):
    sent = {}

    def fake_request(self, endpoint, method="GET", params=None, data=None):
        sent.update(endpoint=endpoint, method=method, data=data)
        return {"foods": [{"fdcId": 1, "description": "Apple, raw", "dataType": "Survey (FNDDS)"}],
                "totalHits": 1, "currentPage": 1, "totalPages": 1}

    monkeypatch.setattr(food_search.FoodClient, "_make_request", fake_request)
    result = food_search.FoodClient("test-key").search("apple", data_type=["SR Legacy"], page_size=10)
    assert sent == {"endpoint": "foods/search", "method": "POST",
                    "data": {"query": "apple", "dataType": ["SR Legacy"], "pageSize": 10, "pageNumber": 1}}
    assert [food.description for food in result.foods] == ["Apple, raw"]


def test_search_falls_back_when_filtered_search_fails(client, monkeypatch):
    class FlakyClient:
        def search(self, query, page_size, data_type=None):
            if data_type:
                raise RuntimeError("USDA rejected the filtered search")
            return SimpleNamespace(foods=[SimpleNamespace(
                fdc_id=7, description="Apple, raw", brand_name=None, data_type="Survey (FNDDS)", gtin_upc=None)])

    monkeypatch.setenv("FDC_API_KEY", "test-key")
    monkeypatch.setattr(food_search, "get_food_client", FlakyClient)
    response = client.get("/api/v1/foods", query_string={"q": "apple"})
    assert response.status_code == 200
    assert [food["fdc_id"] for food in response.json["foods"]] == [7]


def test_usda_answers_are_cached(monkeypatch):
    calls = []

    def fake_request(self, endpoint, method="GET", params=None, data=None):
        calls.append(endpoint)
        if endpoint.startswith("food/"):
            return {"fdcId": 5, "description": "Bananas, raw", "dataType": "SR Legacy", "foodNutrients": []}
        return {"foods": [{"fdcId": 5, "description": "Bananas, raw", "dataType": "SR Legacy"}],
                "totalHits": 1, "currentPage": 1, "totalPages": 1}

    food_search._cache.clear()
    monkeypatch.setattr(food_search.FoodClient, "_make_request", fake_request)
    client = food_search.FoodClient("test-key")
    for _ in range(3):
        assert client.search("Banana ", data_type=["SR Legacy"]).foods[0].fdc_id == 5
        assert client.get_food(5).description == "Bananas, raw"
    assert len(calls) == 2  # one search and one food lookup; the rest came from memory
    food_search._cache.clear()
