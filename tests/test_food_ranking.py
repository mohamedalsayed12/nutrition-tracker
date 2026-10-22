from types import SimpleNamespace

from services.calc import food_measures
from services.food_ranking import rank_foods, stem


def food(fdc_id, description, data_type="SR Legacy", brand_name=None):
    return SimpleNamespace(fdc_id=fdc_id, description=description, data_type=data_type,
                           brand_name=brand_name, gtin_upc=None)


# Real USDA generic results for "milk", in the order USDA returns them.
MILK = [food(1, "Coconut milk", "Survey (FNDDS)"), food(2, "Crackers, milk", "Survey (FNDDS)"),
        food(3, "Goat milk", "Survey (FNDDS)"), food(4, "Milk, human", "Survey (FNDDS)"),
        food(5, "Milk, malted", "Survey (FNDDS)"), food(6, "Milk, NFS", "Survey (FNDDS)"),
        food(7, "Milk, whole", "Survey (FNDDS)"), food(8, "Oat milk", "Survey (FNDDS)"),
        food(9, "Milk dessert, frozen, milk-fat free, chocolate", "Survey (FNDDS)"),
        food(10, "Milk shake with malt", "Survey (FNDDS)"),
        food(11, "Milk, whole, 3.25% milkfat, with added vitamin D", "SR Legacy"),
        food(12, "Whole Milk", "Branded", brand_name="Dairy Farm")]

# Real USDA generic results for "chicken breast".
CHICKEN = [food(21, "Lunchmeat, chicken breast, sliced", "Foundation"),
           food(22, "Chicken breast, rotisserie, skin not eaten", "Survey (FNDDS)"),
           food(23, "Chicken breast tenders, breaded, uncooked"),
           food(24, "Chicken breast, NS as to cooking method, skin not eaten", "Survey (FNDDS)"),
           food(25, "Chicken, breast, boneless, skinless, raw", "Foundation"),
           food(26, "Oscar Mayer, Chicken Breast (honey glazed)")]

APPLE = [food(31, "Apple, candied", "Survey (FNDDS)"), food(32, "Apple juice, 100%", "Survey (FNDDS)"),
         food(33, "Apples, raw, with skin (Includes foods for USDA's Food Distribution Program)"),
         food(34, "Apple, raw", "Survey (FNDDS)"), food(35, "Apples, fuji, with skin, raw", "Foundation"),
         food(36, "Babyfood, apples, dices, toddler"), food(37, "Croissants, apple")]


def ids(foods):
    return [item.fdc_id for item in foods]


def test_everyday_milk_comes_before_other_milks():
    ranked = ids(rank_foods(MILK, "milk"))
    assert ranked[0] == 7                       # "Milk, whole"
    assert ranked.index(7) < ranked.index(1)    # before "Coconut milk"
    assert ranked.index(6) < ranked.index(10)   # "Milk, NFS" before "Milk shake"
    assert ranked.index(4) > ranked.index(5)    # "Milk, human" pushed down
    assert ranked[-1] == 12                     # branded after generic


def test_plain_raw_chicken_breast_comes_first():
    ranked = ids(rank_foods(CHICKEN, "chicken breast"))
    assert ranked[0] == 25                      # "Chicken, breast, boneless, skinless, raw"
    assert ranked.index(22) < ranked.index(23)  # rotisserie before breaded tenders
    assert ranked.index(23) < ranked.index(21)  # anything starting with chicken before lunchmeat


def test_raw_apple_beats_candied_juice_and_baby_food():
    ranked = rank_foods(APPLE, "apple")
    assert ids(ranked)[:3] == [34, 33, 35]     # "Apple, raw", "Apples, raw, with skin", then fuji
    order = ids(ranked)
    assert order.index(31) > order.index(35)    # candied after raw fuji
    assert order.index(36) > order.index(32)    # baby food last among apples


def test_plural_search_and_duplicate_datasets():
    foods = [food(41, "Bananas, raw"), food(42, "Banana, raw", "Survey (FNDDS)"),
             food(43, "Bananas, dehydrated, or banana powder")]
    ranked = ids(rank_foods(foods, "bananas"))
    assert ranked == [41, 43]                   # the FNDDS duplicate of "Bananas, raw" is merged


def test_branded_foods_are_capped_unless_nothing_generic_matches():
    generic = [food(100 + n, f"Rice, white, cooked, variety {n}") for n in range(20)]
    branded = [food(200 + n, f"Rice cakes {n}", "Branded", "Brand") for n in range(10)]
    ranked = rank_foods(generic + branded, "rice")
    assert len(ranked) == 20
    assert sum(item.data_type == "Branded" for item in ranked) == 5
    assert ids(rank_foods(branded, "rice cakes"))[:3] == [200, 201, 202]


def test_only_foods_matching_every_word_are_kept():
    assert ids(rank_foods(MILK, "goat milk")) == [3]
    assert rank_foods(MILK, "   ") == []


def test_stem_handles_simple_plurals():
    assert [stem(w) for w in ("apples", "berries", "tomatoes", "oats", "glass", "egg")] == \
        ["apple", "berry", "tomato", "oat", "glass", "egg"]


def portion(grams, amount=1, modifier="", unit="", description=None):
    return SimpleNamespace(gram_weight=grams, amount=amount, modifier=modifier,
                           measure_unit=unit, portion_description=description)


def test_household_portions_come_first_and_medium_is_default():
    apple = SimpleNamespace(food_portions=[portion(223, modifier="large (3-1/4\" dia)", unit="undetermined"),
                                           portion(182, modifier="medium (3\" dia)", unit="undetermined"),
                                           portion(109, unit="cup, sliced")])
    measures = food_measures(apple)
    labels = [item["label"] for item in measures]
    assert labels[:3] == ['1 large (3-1/4" dia) (223 g)', '1 medium (3" dia) (182 g)', "1 cup, sliced (109 g)"]
    assert [item["label"] for item in measures if item["default"]] == ['1 medium (3" dia) (182 g)']
    assert labels[3:] == ["g", "oz (28.35 g)", "lb (453.59 g)", "100 g"]   # no tablespoons of sliced apple


def test_liquids_get_volume_units_and_plain_foods_default_to_100_g():
    milk = SimpleNamespace(food_portions=[portion(244, unit="cup")])
    codes = [item["code"] for item in food_measures(milk)]
    assert codes[:2] == ["portion:0", "volume:tbsp"]
    assert "volume:ml" in codes and "volume:cup" not in codes
    plain = food_measures(SimpleNamespace(food_portions=[]))
    assert [item["code"] for item in plain if item["default"]] == ["100g"]


# Real USDA results for "rice" (generic part), in the order USDA returned them.
RICE = [food(51, "Rice, fried, NFS", "Survey (FNDDS)"), food(52, "Rice, cooked, NFS", "Survey (FNDDS)"),
        food(53, "Rice, cooked, with milk", "Survey (FNDDS)"),
        food(54, "Rice, white, cooked, glutinous", "Survey (FNDDS)"),
        food(55, "Rice, sweet, cooked with honey", "Survey (FNDDS)"),
        food(56, "Rice, cooked with coconut milk", "Survey (FNDDS)"),
        food(57, "Rice, fried, with chicken", "Survey (FNDDS)"),
        food(58, "Rice, white, long-grain, regular, enriched, cooked"),
        food(59, "Rice noodles, cooked", "Survey (FNDDS)"), food(60, "Rice milk", "Survey (FNDDS)")]


def test_plain_cooked_rice_comes_before_fried_rice_and_rice_dishes():
    ranked = ids(rank_foods(RICE, "rice"))
    assert ranked[0] == 52                      # "Rice, cooked, NFS"
    assert ranked.index(54) < ranked.index(51)  # white rice before fried rice
    assert ranked.index(58) < ranked.index(56)  # plain long-grain before rice with coconut milk
    assert ranked.index(51) < ranked.index(57)  # fried rice before fried rice with chicken
    assert ranked[-2:] == [59, 60]              # rice noodles and rice milk last


# Real USDA results for "salmon" and "bread" (generic part), in USDA's order.
SALMON = [food(71, "Salmon, sockeye, canned, total can contents"),
          food(72, "Salmon, red (sockeye), filets with skin, smoked (Alaska Native)"),
          food(73, "Salmon nuggets, cooked as purchased, unheated", "Survey (FNDDS)"),
          food(74, "Salmon salad", "Survey (FNDDS)"),
          food(75, "Fish, salmon, raw", "Survey (FNDDS)"),
          food(76, "Fish, salmon, pink, raw"), food(77, "Fish, salmon, sockeye, raw")]
BREAD = [food(81, "Bread, sticks, plain"), food(82, "Bread, whole wheat", "Survey (FNDDS)"),
         food(83, "Bread, white", "Survey (FNDDS)"), food(84, "Bread, crumbs, dry, grated, plain"),
         food(85, "Bread, rye", "Survey (FNDDS)")]


def test_raw_salmon_comes_first_even_though_usda_names_it_fish_salmon():
    ranked = ids(rank_foods(SALMON, "salmon"))
    assert ranked[0] == 75                      # "Fish, salmon, raw"
    assert ranked.index(76) < ranked.index(71)  # raw before canned
    assert ranked.index(71) < ranked.index(73)  # canned salmon before salmon nuggets


def test_bread_puts_a_loaf_bread_before_breadsticks_and_crumbs():
    ranked = ids(rank_foods(BREAD, "bread"))
    assert ranked[0] in (82, 83, 85)
    assert ranked[-2:] in ([81, 84], [84, 81])


def test_identical_branded_names_are_shown_once():
    foods = [food(91, "RICE", "Branded", "Store A"), food(92, "RICE", "Branded", "Store A"),
             food(93, "RICE", "Branded", "Store B"), food(94, "Rice, cooked, NFS", "Survey (FNDDS)")]
    assert ids(rank_foods(foods, "rice")) == [94, 91, 93]


def test_white_rice_before_other_raw_rices():
    foods = [food(61, "Rice, black, unenriched, raw"), food(62, "Rice, white, medium-grain, raw, enriched"),
             food(63, "Rice, brown, long-grain, raw"), food(64, "Rice, cooked, NFS", "Survey (FNDDS)")]
    assert ids(rank_foods(foods, "rice"))[0] == 62


def test_from_raw_on_a_cooked_food_does_not_count_as_raw():
    foods = [food(41, "Chicken breast, baked, broiled, or roasted, skin eaten, from raw", "Survey (FNDDS)"),
             food(42, "Chicken, breast, boneless, skinless, raw", "Foundation"),
             food(43, "Chicken breast, rotisserie, skin eaten", "Survey (FNDDS)")]
    assert ids(rank_foods(foods, "chicken breast"))[0] == 42
