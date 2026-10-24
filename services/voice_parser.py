"""Turn a spoken sentence into foods, amounts and a meal.

"I had two scrambled eggs, a slice of toast and 250 ml of milk for breakfast"
-> meal "breakfast", items:
   (2, None, "scrambled eggs"), (1, "slice", "toast"), (250, "ml", "milk")

Plain rules rather than guesswork, so the result is predictable and the app can
say exactly what it understood.
"""

import re
from dataclasses import dataclass
from fractions import Fraction

NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100, "a hundred": 100,
    "half": 0.5, "half a": 0.5, "half an": 0.5, "a half": 0.5, "a quarter": 0.25, "quarter": 0.25,
    "quarter of a": 0.25, "a couple of": 2, "a couple": 2, "couple of": 2, "a few": 3, "a dozen": 12,
    "dozen": 12, "one and a half": 1.5, "two and a half": 2.5, "a single": 1, "some": None,
}

UNITS = {
    "g": "g", "gram": "g", "grams": "g", "gramme": "g", "grammes": "g",
    "kg": "kg", "kilo": "kg", "kilos": "kg", "kilogram": "kg", "kilograms": "kg",
    "oz": "oz", "ounce": "oz", "ounces": "oz",
    "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb",
    "ml": "ml", "millilitre": "ml", "millilitres": "ml", "milliliter": "ml", "milliliters": "ml",
    "l": "l", "litre": "l", "litres": "l", "liter": "l", "liters": "l",
    "cup": "cup", "cups": "cup", "mug": "cup", "mugs": "cup", "glass": "cup", "glasses": "cup",
    "tablespoon": "tbsp", "tablespoons": "tbsp", "tbsp": "tbsp",
    "teaspoon": "tsp", "teaspoons": "tsp", "tsp": "tsp",
    "slice": "slice", "slices": "slice", "piece": "piece", "pieces": "piece",
    "serving": "serving", "servings": "serving", "portion": "serving", "portions": "serving",
    "bowl": "bowl", "bowls": "bowl", "bar": "bar", "bars": "bar", "scoop": "scoop", "scoops": "scoop",
    "can": "can", "cans": "can", "tin": "can", "tins": "can", "bottle": "bottle", "bottles": "bottle",
    "fillet": "fillet", "fillets": "fillet", "handful": "handful", "handfuls": "handful",
    "small": "small", "medium": "medium", "large": "large", "big": "large", "extra large": "extra large",
}

MEALS = {"breakfast": "breakfast", "brunch": "breakfast", "lunch": "lunch", "dinner": "dinner",
         "supper": "dinner", "tea": "dinner", "snack": "snack", "snacks": "snack", "dessert": "snack"}

LEAD_INS = re.compile(
    r"^(?:(?:hey\s+)?(?:siri\s*,?\s*)?)?(?:please\s+)?(?:log|add|record|track)?\s*"
    r"(?:that\s+)?(?:i(?:'ve| have)?\s+(?:just\s+)?(?:had|ate|eaten|drank|drunk|eat|drink|have)|"
    r"i\s+just\s+(?:had|ate|drank)|for\s+(?:breakfast|lunch|dinner)\s+i\s+(?:had|ate))?\s*",
    re.IGNORECASE,
)

_NUMBER = r"\d+\s+\d+\s*/\s*\d+|\d+\s*/\s*\d+|\d+(?:\.\d+)?"
_WORD_NUMBERS = "|".join(sorted((re.escape(w) for w in NUMBER_WORDS), key=len, reverse=True))
_UNIT_WORDS = "|".join(sorted((re.escape(w) for w in UNITS), key=len, reverse=True))
_QUANTITY = re.compile(rf"^(?:(?P<num>{_NUMBER})(?=[a-z\s]|$)|(?P<word>{_WORD_NUMBERS})\b)\s*", re.IGNORECASE)
_UNIT = re.compile(rf"^(?P<unit>{_UNIT_WORDS})\b\.?\s*(?:of\s+)?", re.IGNORECASE)
_STARTS_WITH_AMOUNT = re.compile(rf"^(?:{_NUMBER}|{_WORD_NUMBERS})\b", re.IGNORECASE)


@dataclass
class SpokenItem:
    quantity: float | None
    unit: str | None
    food: str
    said: str


def parse_meal_text(text):
    """(meal or None, [SpokenItem]) from what was said."""
    text = " ".join(str(text).replace("’", "'").split())
    text = _join_halves(text)
    meal, text = _take_meal(text)
    text = LEAD_INS.sub("", text, count=1).strip(" .,!?")
    items = []
    for chunk in _split_items(text):
        item = _parse_item(chunk)
        if item is not None:
            items.append(item)
    return meal, items


def _take_meal(text):
    pattern = re.compile(r"\b(?:(?:for|at|during|as(?:\s+a)?|my)\s+(breakfast|brunch|lunch|dinner|supper|snacks?|dessert)|for\s+(tea))\b",
                         re.IGNORECASE)
    match = pattern.search(text)
    if match is None:
        lead = re.match(r"^(breakfast|brunch|lunch|dinner|supper|snacks?)\s*[:,-]?\s+", text, re.IGNORECASE)
        if lead is None:
            return None, text
        return MEALS[lead.group(1).lower()], text[lead.end():]
    word = (match.group(1) or match.group(2)).lower()
    return MEALS[word], (text[:match.start()] + " " + text[match.end():]).strip()


def _join_halves(text):
    """"one and a half cups" -> "1.5 cups", so the "and" isn't read as a second food."""
    def replace(match):
        whole = _number(match.group(1))
        return f"{whole + 0.5:g}" if whole is not None else match.group(0)
    return re.sub(rf"\b(\d+|{_WORD_NUMBERS})\s+and\s+a\s+half\b", replace, text, flags=re.IGNORECASE)


def _split_items(text):
    """Split on commas, "plus", "then", and on "and"/"with" only when an amount follows,
    so "fish and chips" and "mac and cheese" stay whole."""
    chunks = re.split(r"\s*(?:,|;|\bplus\b|\bthen\b|\band then\b|&)\s*", text, flags=re.IGNORECASE)
    items = []
    for chunk in chunks:
        chunk = re.sub(r"^(?:and|with)\s+", "", chunk.strip(), flags=re.IGNORECASE)
        parts = re.split(r"\s+(?:and|with|along with)\s+(?=(?:" + _NUMBER + "|" + _WORD_NUMBERS + r")\b)",
                         chunk, flags=re.IGNORECASE)
        items.extend(part.strip() for part in parts if part.strip())
    return items


def _parse_item(chunk):
    said = chunk
    quantity = None
    rest = chunk
    match = _QUANTITY.match(rest)
    if match:
        quantity = _number(match.group("num") or match.group("word"))
        rest = rest[match.end():]
    unit = None
    sized = _QUANTITY.match(rest)
    if sized and sized.group("num"):
        size_unit = _UNIT.match(rest[sized.end():])
        if size_unit and UNITS[size_unit.group("unit").lower()] in ("g", "kg", "oz", "lb", "ml", "l"):
            quantity = (quantity or 1) * _number(sized.group("num"))
            unit = UNITS[size_unit.group("unit").lower()]
            rest = rest[sized.end() + size_unit.end():]
            rest = re.sub(r"^(?:cans?|tins?|bottles?|glass(?:es)?|cartons?|packs?|pots?|bags?|bars?|pieces?)\s+(?:of\s+)?", "",
                          rest, flags=re.IGNORECASE)
    match = None if unit else _UNIT.match(rest)
    if match:
        unit = UNITS[match.group("unit").lower()]
        rest = rest[match.end():]
    rest = re.sub(r"^(?:of\s+)", "", rest, flags=re.IGNORECASE)
    food = re.sub(r"[^\w\s%'-]", " ", rest)
    food = " ".join(food.split()).strip()
    food = re.sub(r"^(?:the|my|some)\s+", "", food, flags=re.IGNORECASE)
    if len(food) < 2:
        return None
    return SpokenItem(quantity=quantity, unit=unit, food=food, said=said)


def _number(value):
    value = value.lower().strip()
    if value in NUMBER_WORDS:
        return NUMBER_WORDS[value]
    mixed = re.fullmatch(r"(\d+)\s+(\d+)\s*/\s*(\d+)", value)
    if mixed:
        return int(mixed.group(1)) + float(Fraction(int(mixed.group(2)), int(mixed.group(3))))
    if "/" in value:
        top, bottom = (int(part) for part in value.split("/"))
        return float(Fraction(top, bottom)) if bottom else None
    return float(value)
