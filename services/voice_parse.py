"""Parse spoken food logs into search query, grams, and meal."""

import re

MEAL_WORDS = {
    "breakfast": "breakfast",
    "lunch": "lunch",
    "dinner": "dinner",
    "supper": "dinner",
    "snack": "snack",
    "brunch": "breakfast",
}

UNIT_TO_GRAMS = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "ounce": 28.3495,
    "ounces": 28.3495,
    "oz": 28.3495,
    "lb": 453.592,
    "pound": 453.592,
    "pounds": 453.592,
    "cup": 240.0,
    "cups": 240.0,
    "tbsp": 15.0,
    "tablespoon": 15.0,
    "tablespoons": 15.0,
    "tsp": 5.0,
    "teaspoon": 5.0,
    "teaspoons": 5.0,
}

FILLER = re.compile(
    r"\b(i|i'd|i've|im|i'm|ate|eaten|had|have|just|like|please|log|add|"
    r"track|of|some|a|an|the|for|me|my|today|this|morning|afternoon|evening|"
    r"night|about|around|roughly|maybe)\b",
    re.IGNORECASE,
)

NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "half": 0.5,
}


def _to_number(token):
    token = token.lower().replace(",", "")
    if token in NUMBER_WORDS:
        return float(NUMBER_WORDS[token])
    if re.fullmatch(r"\d+(?:\.\d+)?", token):
        return float(token)
    if re.fullmatch(r"\d+/\d+", token):
        numerator, denominator = token.split("/")
        return float(numerator) / float(denominator)
    return None


def parse_voice_log(transcript, default_meal="snack"):
    text = " ".join(str(transcript or "").strip().split())
    if not text:
        raise ValueError("Say what you ate, for example: 180 grams of chicken for dinner.")

    lower = text.lower()
    meal = default_meal
    for word, value in MEAL_WORDS.items():
        if re.search(rf"\b{word}\b", lower):
            meal = value
            break

    grams = None
    amount_match = re.search(
        r"(?P<qty>\d+(?:\.\d+)?|\d+/\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|half)"
        r"\s*(?P<unit>g|grams?|kg|ounces?|oz|lbs?|pounds?|cups?|tbsp|tablespoons?|tsp|teaspoons?)\b",
        lower,
    )
    if amount_match:
        qty = _to_number(amount_match.group("qty"))
        unit = amount_match.group("unit")
        if unit.startswith("lb"):
            unit = "lb"
        elif unit.startswith("pound"):
            unit = "pound"
        elif unit.startswith("ounce"):
            unit = "ounce"
        elif unit == "oz":
            unit = "oz"
        elif unit.startswith("cup"):
            unit = "cup"
        elif unit.startswith("table") or unit == "tbsp":
            unit = "tbsp"
        elif unit.startswith("tea") or unit == "tsp":
            unit = "tsp"
        elif unit.startswith("gram") or unit == "g":
            unit = "g"
        if qty is not None and unit in UNIT_TO_GRAMS:
            grams = round(qty * UNIT_TO_GRAMS[unit], 1)

    # Counted items without an explicit unit, e.g. "two eggs"
    if grams is None:
        count_match = re.search(
            r"\b(?P<qty>a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+"
            r"(?P<item>eggs?|bananas?|apples?|oranges?)\b",
            lower,
        )
        if count_match:
            qty = _to_number(count_match.group("qty")) or 1
            item = count_match.group("item")
            typical = {"egg": 50, "banana": 120, "apple": 180, "orange": 130}
            key = item.rstrip("s")
            grams = round(qty * typical.get(key, 100), 1)

    food_text = lower
    for word in MEAL_WORDS:
        food_text = re.sub(rf"\b{word}\b", " ", food_text)
    if amount_match:
        food_text = food_text[:amount_match.start()] + " " + food_text[amount_match.end():]
    food_text = FILLER.sub(" ", food_text)
    food_text = re.sub(r"[^a-z0-9\s-]", " ", food_text)
    food_query = " ".join(food_text.split())
    if not food_query:
        raise ValueError("Could not tell which food to log. Try: chicken breast 180 grams.")

    return {
        "transcript": text,
        "food_query": food_query,
        "grams": grams if grams and grams > 0 else 100.0,
        "meal": meal,
        "grams_inferred": grams is not None,
    }
