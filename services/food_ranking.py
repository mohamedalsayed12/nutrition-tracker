"""Rank USDA search results so everyday foods come first, as Cronometer does.

USDA's own search order is a text-relevance score, so a search for "milk" can
return "Coconut milk" and "Crackers, milk" before "Milk, whole". This module
re-orders the results with simple rules that can be explained and tested:

1. Match: the food's name starts with what was typed ("Milk, whole") beats a
   name that starts with it but adds more words ("Milk shake"), which beats a
   name that only contains it ("Goat milk").
2. Everyday versions: processed or unusual variants that were not asked for
   ("candied", "dessert", "baby food") are pushed down, and plain versions
   ("raw", "whole", "cooked", "NFS") are lifted.
3. Simpler names win ties: fewer extra words.
4. Source: USDA SR Legacy and Foundation (lab-analysed) before Survey (FNDDS),
   and all generic foods before branded products.

Duplicates of the same food from different USDA datasets ("Bananas, raw" and
"Banana, raw") are merged, keeping the higher-ranked one.
"""

import re

# Words that make a food a processed or unusual variant. A food is pushed down
# for each one it contains that the search did not ask for.
UNUSUAL = {
    "baby", "infant", "toddler", "formula", "human", "dessert", "candied", "candy", "candies",
    "pie", "cake", "cookie", "cracker", "pudding", "supplement", "substitute", "imitation",
    "bar", "snack", "cereal", "flavored", "flavor", "usda", "commodity", "school", "lunch",
}
PROCESSED = {
    "canned", "dried", "dehydrated", "frozen", "juice", "sauce", "breaded", "coated", "glazed",
    "sweetened", "syrup", "powder", "concentrate", "malted", "evaporated", "condensed",
    "pickled", "smoked", "spread", "mix", "prepared", "fat-free", "nonfat", "light", "fried",
}
# Small words that don't make a name more specific, so they are not counted as
# extra words. "with" and "and" do mark a mixed dish ("Rice, cooked with milk"),
# which counts as a processed variant instead.
FILLER = {"with", "and", "or", "as", "to", "from", "of", "in", "the", "a", "ns", "nfs", "made", "type"}
MIXED_DISH = {"with", "and"}
# Words that describe the plain, everyday version of a food. "Raw", "whole" and
# "plain" are the most typical choice; a cooking method or "NFS" (not further
# specified) is a good generic match but slightly less so.
EVERYDAY = {"raw": 2, "whole": 2, "plain": 2, "fresh": 2,
            "cooked": 1, "boiled": 1, "baked": 1, "roasted": 1, "nfs": 1, "white": 1}

DATA_TYPE_ORDER = {"SR Legacy": 0, "Foundation": 1, "Survey (FNDDS)": 2, "Branded": 3}

GENERIC_RESULTS = 15
BRANDED_RESULTS = 5
MAX_RESULTS = GENERIC_RESULTS + BRANDED_RESULTS


def stem(word):
    """Reduce simple English plurals so "apples" matches "apple"."""
    word = word.lower()
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("oes"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def words(text):
    return [stem(word) for word in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", (text or "").lower())]


def matches(food, query_words):
    """True when every searched word starts some word of the food's name or brand."""
    food_words = words(f"{food.description} {getattr(food, 'brand_name', None) or ''}")
    return all(any(word.startswith(query_word) for word in food_words) for query_word in query_words)


def _match_tier(description, query_words):
    segments = [words(segment) for segment in description.split(",")]
    first_words = segments[0] if segments else []
    if not first_words or first_words[0] != query_words[0]:
        return 2  # the name only contains the search, e.g. "Goat milk"
    head = set(first_words) | (set(segments[1]) if len(segments) > 1 and len(first_words) == 1 else set())
    if set(query_words) <= head and len(set(first_words) - set(query_words)) == 0:
        return 0  # "Milk, whole", "Chicken, breast, raw", "Chicken breast, grilled"
    return 1      # starts with the search but adds words, e.g. "Milk shake"


def rank_key(food, query_words):
    # Text in brackets is a USDA note, e.g. "(Includes foods for USDA's Food
    # Distribution Program)", not part of the food's name.
    description = re.sub(r"\([^)]*\)", "", food.description or "").strip()
    food_words = set(words(description))
    asked = set(query_words)
    unusual = sum(1 for word in food_words - asked if word in UNUSUAL)
    processed = sum(1 for word in food_words - asked if word in PROCESSED)
    processed += 1 if (food_words - asked) & MIXED_DISH else 0
    everyday = max((EVERYDAY.get(word, 0) for word in food_words - asked), default=0)
    extra_words = len(food_words - asked - FILLER)
    return (
        _match_tier(description, query_words),
        2 * unusual + processed,
        -everyday,
        extra_words,
        DATA_TYPE_ORDER.get(food.data_type, 4),
        len(description),
    )


def _same_food_key(food):
    return tuple(sorted(set(words(food.description)) - {"nfs", "ns"}))


def rank_foods(foods, query):
    """Matching foods, everyday generic foods first, then a few branded ones."""
    query_words = words(" ".join(query.split()))
    if not query_words:
        return []
    candidates = [food for food in foods if matches(food, query_words)]
    candidates.sort(key=lambda food: rank_key(food, query_words))

    generic, branded, seen = [], [], set()
    for food in candidates:
        key = _same_food_key(food) if food.data_type != "Branded" else ("branded", food.fdc_id)
        if key in seen:
            continue
        seen.add(key)
        (branded if food.data_type == "Branded" else generic).append(food)

    selected = generic[:GENERIC_RESULTS] + branded[:BRANDED_RESULTS]
    if len(selected) < MAX_RESULTS:
        leftover = generic[GENERIC_RESULTS:] + branded[BRANDED_RESULTS:]
        selected.extend(leftover[:MAX_RESULTS - len(selected)])
    return selected
