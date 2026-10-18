"""Food suggestions for each tracked micronutrient.

Used when daily progress is below the target so the app can advise foods that
help close the gap. Suggestions are educational food ideas, not medical advice
or prescribed meal plans.
"""

DEFICIENCY_PERCENT_THRESHOLD = 100

# name -> list of {food, reason}
NUTRIENT_FOOD_RECOMMENDATIONS = {
    "Vitamin A": [
        {"food": "Sweet potato", "reason": "High in beta-carotene, which the body converts to vitamin A."},
        {"food": "Carrots", "reason": "A convenient beta-carotene source for vitamin A."},
        {"food": "Spinach or kale", "reason": "Leafy greens provide provitamin A carotenoids."},
        {"food": "Eggs", "reason": "Provide preformed vitamin A (retinol)."},
    ],
    "Thiamin (B1)": [
        {"food": "Pork loin", "reason": "One of the richest common food sources of thiamin."},
        {"food": "Sunflower seeds", "reason": "Plant source with meaningful thiamin."},
        {"food": "Fortified breakfast cereal", "reason": "Often enriched with thiamin."},
        {"food": "Black beans", "reason": "Legumes contribute thiamin in plant-based meals."},
    ],
    "Riboflavin (B2)": [
        {"food": "Milk or yogurt", "reason": "Dairy is a reliable riboflavin source."},
        {"food": "Eggs", "reason": "Provide riboflavin with protein."},
        {"food": "Almonds", "reason": "A plant-based riboflavin option."},
        {"food": "Mushrooms", "reason": "Contribute riboflavin in savory meals."},
    ],
    "Niacin (B3)": [
        {"food": "Chicken breast", "reason": "Poultry is rich in niacin."},
        {"food": "Tuna", "reason": "Fish provides concentrated niacin."},
        {"food": "Peanuts", "reason": "A plant food with useful niacin."},
        {"food": "Brown rice", "reason": "Whole grains help meet niacin needs."},
    ],
    "Pantothenic acid (B5)": [
        {"food": "Avocado", "reason": "Provides pantothenic acid in a plant food."},
        {"food": "Chicken", "reason": "Poultry contributes vitamin B5."},
        {"food": "Mushrooms", "reason": "A solid plant source of pantothenic acid."},
        {"food": "Eggs", "reason": "Help raise B5 alongside other B vitamins."},
    ],
    "Vitamin B6": [
        {"food": "Chickpeas", "reason": "Legumes are a strong B6 source."},
        {"food": "Banana", "reason": "An easy everyday B6 contributor."},
        {"food": "Salmon", "reason": "Fish provides vitamin B6 with protein."},
        {"food": "Potato", "reason": "Starchy vegetables add B6."},
    ],
    "Biotin (B7)": [
        {"food": "Eggs", "reason": "Egg yolks are among the best biotin sources."},
        {"food": "Salmon", "reason": "Fish contributes biotin."},
        {"food": "Sunflower seeds", "reason": "Seeds help raise biotin intake."},
        {"food": "Sweet potato", "reason": "A plant food with useful biotin."},
    ],
    "Folate (B9)": [
        {"food": "Lentils", "reason": "Legumes are folate-dense."},
        {"food": "Spinach", "reason": "Leafy greens provide folate."},
        {"food": "Asparagus", "reason": "A vegetable high in folate."},
        {"food": "Fortified grains", "reason": "Many breads and cereals are folate-fortified."},
    ],
    "Vitamin C": [
        {"food": "Orange or orange juice", "reason": "Classic vitamin C source that also helps iron absorption."},
        {"food": "Bell peppers", "reason": "Especially red peppers are very high in vitamin C."},
        {"food": "Strawberries", "reason": "Berries raise vitamin C with fiber."},
        {"food": "Broccoli", "reason": "A vegetable source of vitamin C."},
    ],
    "Vitamin D": [
        {"food": "Fatty fish (salmon, sardines)", "reason": "Among the few rich natural food sources of vitamin D."},
        {"food": "Fortified milk or plant milk", "reason": "Common fortified option for vitamin D."},
        {"food": "Egg yolks", "reason": "Provide some vitamin D."},
        {"food": "Fortified cereal", "reason": "Can help fill vitamin D gaps from food."},
    ],
    "Vitamin E": [
        {"food": "Sunflower seeds", "reason": "Very high in vitamin E."},
        {"food": "Almonds", "reason": "Nuts are a practical vitamin E source."},
        {"food": "Peanut butter", "reason": "Contributes vitamin E in everyday meals."},
        {"food": "Spinach", "reason": "Leafy greens add vitamin E."},
    ],
    "Vitamin K": [
        {"food": "Kale", "reason": "Leafy greens are rich in vitamin K1 (phylloquinone)."},
        {"food": "Spinach", "reason": "A high-K1 vegetable for daily meals."},
        {"food": "Broccoli", "reason": "Provides vitamin K1 with fiber."},
        {"food": "Brussels sprouts", "reason": "Another strong K1 vegetable."},
    ],
    "Vitamin K2": [
        {"food": "Natto (fermented soybeans)", "reason": "One of the richest dietary sources of MK-7 (vitamin K2)."},
        {"food": "Hard cheeses (Gouda, Edam)", "reason": "Fermented cheeses provide menaquinones."},
        {"food": "Egg yolks", "reason": "Contain some vitamin K2."},
        {"food": "Chicken (dark meat)", "reason": "Poultry contributes menaquinones, especially MK-4."},
    ],
    "Vitamin B12": [
        {"food": "Clams or mussels", "reason": "Shellfish are extremely high in B12."},
        {"food": "Salmon or tuna", "reason": "Fish reliably provides B12."},
        {"food": "Eggs", "reason": "Help raise B12 in mixed diets."},
        {"food": "Fortified nutritional yeast or plant milk", "reason": "Important B12 option for vegetarian/vegan patterns."},
    ],
    "Choline": [
        {"food": "Eggs", "reason": "Egg yolks are among the best choline sources."},
        {"food": "Beef liver", "reason": "Extremely high in choline if you eat organ meats."},
        {"food": "Soybeans / edamame", "reason": "A strong plant choline source."},
        {"food": "Chicken breast", "reason": "Poultry contributes choline with protein."},
    ],
    "Calcium": [
        {"food": "Milk, yogurt, or kefir", "reason": "Dairy is a concentrated calcium source."},
        {"food": "Fortified plant milk", "reason": "Useful calcium option if you avoid dairy."},
        {"food": "Tofu set with calcium", "reason": "Check the label; calcium-set tofu is high."},
        {"food": "Canned sardines with bones", "reason": "Soft bones provide absorbable calcium."},
    ],
    "Chloride": [
        {"food": "Table salt (in moderation)", "reason": "Most chloride comes from sodium chloride."},
        {"food": "Seaweed", "reason": "Contributes chloride and other minerals."},
        {"food": "Tomatoes", "reason": "Vegetables add some chloride without heavy salt."},
        {"food": "Celery", "reason": "A vegetable source of chloride."},
    ],
    "Chromium": [
        {"food": "Broccoli", "reason": "A vegetable with useful chromium."},
        {"food": "Grape juice", "reason": "Can contribute chromium."},
        {"food": "Whole-wheat bread", "reason": "Whole grains provide chromium."},
        {"food": "Turkey breast", "reason": "Poultry adds some chromium."},
    ],
    "Copper": [
        {"food": "Liver", "reason": "Extremely high in copper if you eat organ meats."},
        {"food": "Oysters or shellfish", "reason": "Seafood is copper-rich."},
        {"food": "Cashews", "reason": "Nuts help raise copper."},
        {"food": "Dark chocolate", "reason": "A concentrated plant copper source."},
    ],
    "Fluoride": [
        {"food": "Fluoridated tap water", "reason": "Often the main dietary fluoride source."},
        {"food": "Brewed tea", "reason": "Tea leaves accumulate fluoride."},
        {"food": "Canned seafood with bones", "reason": "Contributes some fluoride."},
        {"food": "Fluoride toothpaste (not swallowed)", "reason": "Dental fluoride is separate from diet targets."},
    ],
    "Iodine": [
        {"food": "Iodized salt", "reason": "A simple way to meet iodine needs."},
        {"food": "Seaweed (nori, wakame)", "reason": "Very high in iodine; use moderate portions."},
        {"food": "Cod or other white fish", "reason": "Seafood provides iodine."},
        {"food": "Dairy milk or yogurt", "reason": "Dairy often contributes iodine."},
    ],
    "Iron": [
        {"food": "Lean beef or lamb", "reason": "Heme iron is absorbed efficiently."},
        {"food": "Lentils or chickpeas", "reason": "Plant iron; pair with vitamin C for better absorption."},
        {"food": "Spinach", "reason": "Nonheme iron source; combine with citrus or peppers."},
        {"food": "Fortified breakfast cereal", "reason": "Often provides a large share of daily iron."},
    ],
    "Magnesium": [
        {"food": "Pumpkin seeds", "reason": "Seeds are magnesium-dense."},
        {"food": "Almonds", "reason": "Nuts help raise magnesium."},
        {"food": "Black beans", "reason": "Legumes contribute magnesium and fiber."},
        {"food": "Spinach", "reason": "Leafy greens add magnesium."},
    ],
    "Manganese": [
        {"food": "Pineapple", "reason": "Fruit source of manganese."},
        {"food": "Oats", "reason": "Whole grains provide manganese."},
        {"food": "Pecans", "reason": "Nuts are manganese-rich."},
        {"food": "Brown rice", "reason": "Contributes manganese in grain meals."},
    ],
    "Molybdenum": [
        {"food": "Lentils", "reason": "Legumes are strong molybdenum sources."},
        {"food": "Black-eyed peas", "reason": "Help meet molybdenum needs."},
        {"food": "Yogurt", "reason": "Dairy contributes molybdenum."},
        {"food": "Potatoes", "reason": "A common food with useful molybdenum."},
    ],
    "Phosphorus": [
        {"food": "Dairy milk or yogurt", "reason": "Dairy is phosphorus-rich."},
        {"food": "Salmon", "reason": "Fish provides phosphorus with protein."},
        {"food": "Chicken", "reason": "Poultry contributes phosphorus."},
        {"food": "Lentils", "reason": "Plant meals can raise phosphorus."},
    ],
    "Potassium": [
        {"food": "Potato or sweet potato", "reason": "Starchy vegetables are potassium-dense."},
        {"food": "Banana", "reason": "A convenient potassium source."},
        {"food": "Beans or lentils", "reason": "Legumes raise potassium and fiber."},
        {"food": "Avocado", "reason": "Provides potassium in savory meals."},
    ],
    "Selenium": [
        {"food": "Brazil nuts (1–2)", "reason": "Extremely high in selenium; a small portion is enough."},
        {"food": "Tuna or sardines", "reason": "Seafood reliably provides selenium."},
        {"food": "Eggs", "reason": "Contribute selenium in everyday diets."},
        {"food": "Sunflower seeds", "reason": "A plant option for selenium."},
    ],
    "Sodium": [
        {"food": "Fresh fruits and vegetables", "reason": "Naturally low in sodium when you are over the limit."},
        {"food": "Unsalted nuts or seeds", "reason": "Snack options without added salt."},
        {"food": "Home-cooked meals", "reason": "Let you control added salt versus packaged foods."},
        {"food": "Herbs and spices instead of salt", "reason": "Flavor food while lowering sodium."},
    ],
    "Zinc": [
        {"food": "Oysters", "reason": "The richest common zinc food."},
        {"food": "Beef", "reason": "Red meat is a reliable zinc source."},
        {"food": "Pumpkin seeds", "reason": "A strong plant zinc option."},
        {"food": "Chickpeas", "reason": "Legumes help raise zinc in plant-forward diets."},
    ],
}


def foods_for_nutrient(name):
    return list(NUTRIENT_FOOD_RECOMMENDATIONS.get(name, ()))


def all_nutrient_food_recommendations():
    return {name: foods_for_nutrient(name) for name in NUTRIENT_FOOD_RECOMMENDATIONS}


def is_deficient(row):
    """True when intake is below a minimum target or above a maximum (sodium)."""
    percent = row.get("percent")
    if percent is None:
        return False
    if row.get("limit") or row.get("direction") == "maximum":
        return percent > DEFICIENCY_PERCENT_THRESHOLD
    return percent < DEFICIENCY_PERCENT_THRESHOLD


def attach_food_recommendations(progress_rows):
    """Copy progress rows and add food advice for nutrients that need attention."""
    enriched = []
    for row in progress_rows:
        item = dict(row)
        foods = foods_for_nutrient(item["name"])
        item["food_recommendations"] = foods
        if is_deficient(item) and foods:
            if item.get("limit") or item.get("direction") == "maximum":
                item["advice"] = (
                    f"You are above your {item['name']} limit. Prefer lower-sodium choices."
                )
            else:
                remaining = item.get("remaining")
                unit = item.get("unit", "")
                gap = f" about {remaining} {unit} more" if remaining is not None else ""
                item["advice"] = (
                    f"You are below your {item['name']} target{gap}. "
                    f"Try foods like {', '.join(food['food'] for food in foods[:3])}."
                )
            item["deficient"] = True
        else:
            item["deficient"] = bool(is_deficient(item))
            if item["deficient"]:
                item["advice"] = f"You are outside your {item['name']} target."
            else:
                item["advice"] = None
        enriched.append(item)
    return enriched


def deficiency_advice(progress_rows):
    """Return only nutrients that need food advice right now."""
    return [row for row in attach_food_recommendations(progress_rows) if row.get("deficient")]
