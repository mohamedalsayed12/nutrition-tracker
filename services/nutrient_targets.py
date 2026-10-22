AGE_BAND_ENDS = (3, 8, 13, 18, 30, 50, 70)

MICRONUTRIENTS = (
    ("Vitamin A", "mcg RAE", 900, ((300, 300), (400, 400), (600, 600), (900, 700), (900, 700), (900, 700), (900, 700), (900, 700)), "https://ods.od.nih.gov/factsheets/VitaminA-Consumer/"),
    ("Thiamin (B1)", "mg", 1.2, ((0.5, 0.5), (0.6, 0.6), (0.9, 0.9), (1.2, 1.0), (1.2, 1.1), (1.2, 1.1), (1.2, 1.1), (1.2, 1.1)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Riboflavin (B2)", "mg", 1.3, ((0.5, 0.5), (0.6, 0.6), (0.9, 0.9), (1.3, 1.0), (1.3, 1.1), (1.3, 1.1), (1.3, 1.1), (1.3, 1.1)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Niacin (B3)", "mg NE", 16, ((6, 6), (8, 8), (12, 12), (16, 14), (16, 14), (16, 14), (16, 14), (16, 14)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Pantothenic acid (B5)", "mg", 5, ((2, 2), (3, 3), (4, 4), (5, 5), (5, 5), (5, 5), (5, 5), (5, 5)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Vitamin B6", "mg", 1.7, ((0.5, 0.5), (0.6, 0.6), (1, 1), (1.3, 1.2), (1.3, 1.3), (1.3, 1.3), (1.7, 1.5), (1.7, 1.5)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Folate (B9)", "mcg DFE", 400, ((150, 150), (200, 200), (300, 300), (400, 400), (400, 400), (400, 400), (400, 400), (400, 400)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Vitamin C", "mg", 90, ((15, 15), (25, 25), (45, 45), (75, 65), (90, 75), (90, 75), (90, 75), (90, 75)), "https://ods.od.nih.gov/factsheets/VitaminC-Consumer/"),
    ("Vitamin D", "mcg", 20, ((15, 15), (15, 15), (15, 15), (15, 15), (15, 15), (15, 15), (15, 15), (20, 20)), "https://ods.od.nih.gov/factsheets/VitaminD-Consumer/"),
    ("Vitamin E", "mg", 15, ((6, 6), (7, 7), (11, 11), (15, 15), (15, 15), (15, 15), (15, 15), (15, 15)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Vitamin K", "mcg", 120, ((30, 30), (55, 55), (60, 60), (75, 75), (120, 90), (120, 90), (120, 90), (120, 90)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Vitamin B12", "mcg", 2.4, ((0.9, 0.9), (1.2, 1.2), (1.8, 1.8), (2.4, 2.4), (2.4, 2.4), (2.4, 2.4), (2.4, 2.4), (2.4, 2.4)), "https://ods.od.nih.gov/factsheets/VitaminB12-Consumer/"),
    ("Choline", "mg", 550, ((200, 200), (250, 250), (375, 375), (550, 400), (550, 425), (550, 425), (550, 425), (550, 425)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Calcium", "mg", 1300, ((700, 700), (1000, 1000), (1300, 1300), (1300, 1300), (1000, 1000), (1000, 1000), (1000, 1200), (1200, 1200)), "https://ods.od.nih.gov/factsheets/Calcium-HealthProfessional/"),
    ("Copper", "mg", 0.9, ((0.34, 0.34), (0.44, 0.44), (0.7, 0.7), (0.89, 0.89), (0.9, 0.9), (0.9, 0.9), (0.9, 0.9), (0.9, 0.9)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Iron", "mg", 18, ((7, 7), (10, 10), (8, 8), (11, 15), (8, 18), (8, 18), (8, 8), (8, 8)), "https://ods.od.nih.gov/factsheets/Iron-Consumer/"),
    ("Magnesium", "mg", 420, ((80, 80), (130, 130), (240, 240), (410, 360), (400, 310), (420, 320), (420, 320), (420, 320)), "https://ods.od.nih.gov/factsheets/Magnesium-HealthProfessional/"),
    ("Manganese", "mg", 2.3, ((1.2, 1.2), (1.5, 1.5), (1.9, 1.6), (2.2, 1.6), (2.3, 1.8), (2.3, 1.8), (2.3, 1.8), (2.3, 1.8)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Phosphorus", "mg", 1250, ((460, 460), (500, 500), (1250, 1250), (1250, 1250), (700, 700), (700, 700), (700, 700), (700, 700)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Potassium", "mg", 4700, ((2000, 2000), (2300, 2300), (2500, 2300), (3000, 2300), (3400, 2600), (3400, 2600), (3400, 2600), (3400, 2600)), "https://ods.od.nih.gov/factsheets/Potassium-Consumer/"),
    ("Selenium", "mcg", 55, ((20, 20), (30, 30), (40, 40), (55, 55), (55, 55), (55, 55), (55, 55), (55, 55)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Sodium", "mg", 2300, ((1200, 1200), (1500, 1500), (1800, 1800), (2300, 2300), (2300, 2300), (2300, 2300), (2300, 2300), (2300, 2300)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Zinc", "mg", 11, ((3, 3), (5, 5), (8, 8), (11, 9), (11, 8), (11, 8), (11, 8), (11, 8)), "https://ods.od.nih.gov/factsheets/Zinc-Consumer/"),
)


PREGNANCY_SOURCE = "https://ods.od.nih.gov/factsheets/Pregnancy-HealthProfessional/"
CONDITION_MICRONUTRIENTS = {
    "pregnancy": {
        "label": "Pregnancy",
        "source": PREGNANCY_SOURCE,
        "summary": "Pregnancy reference targets are applied automatically. Review prenatal nutrition with your care team, including folate, iron, iodine, choline, vitamin D, and calcium. Iodine isn't tracked here, so ask about it too.",
        "nutrients": {
            "Folate (B9)": "Supports early neural tube development; the published pregnancy reference is 600 mcg DFE/day.",
            "Iron": "Needs rise with blood volume and fetal development; the published pregnancy reference is 27 mg/day.",
            "Choline": "Supports fetal development; the published pregnancy reference is 450 mg/day.",
            "Vitamin D": "Supports calcium absorption and bone health; the pregnancy reference remains 15 mcg/day.",
            "Calcium": "Supports bone health; pregnancy uses 1,300 mg/day for ages 14–18 and 1,000 mg/day for adults.",
        },
    },
    "diabetes": {
        "label": "Diabetes",
        "source": "https://diabetesjournals.org/care/article/49/Supplement_1/S50/163924/3-Prevention-or-Delay-of-Diabetes-and-Associated",
        "summary": "If you take metformin long term, discuss periodic vitamin B12 testing with your clinician. Diabetes alone does not set a higher B12 intake target here.",
        "nutrients": {
            "Vitamin B12": "Long-term metformin use can affect B12 status. Food intake progress cannot show whether B12 absorption or blood levels are adequate.",
        },
    },
    "ibs": {
        "label": "IBS",
        "source": "https://www.monashfodmap.com/blog/research-update-occurrence-micronutrient-deficiencies-ibs/",
        "summary": "Restrictive IBS diets can leave gaps in calcium, iron, folate, thiamin, riboflavin, and magnesium. These keep their usual reference targets; a dietitian can help maintain adequate intake while managing symptoms.",
        "nutrients": {
            "Calcium": "Pay attention to calcium adequacy if you restrict dairy; suitable fortified alternatives can help.",
            "Iron": "Restrictive IBS diets can reduce iron intake; review adequacy against your personal target.",
            "Folate (B9)": "Restrictive IBS diets can reduce folate intake; review adequacy against your personal target.",
            "Thiamin (B1)": "Restrictive IBS diets can reduce thiamin intake; review adequacy against your personal target.",
            "Riboflavin (B2)": "Restrictive IBS diets can reduce riboflavin intake; review adequacy against your personal target.",
            "Magnesium": "Restrictive IBS diets can reduce magnesium intake; review adequacy against your personal target.",
        },
    },
    "menstruation": {
        "label": "Periods / menstruation",
        "source": "https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/",
        "summary": "Periods raise the iron target to the menstrual reference when that is higher: 15 mg/day at ages 14–18 and 18 mg/day from age 19. Vitamin C keeps its usual target (65 mg/day at ages 14–18, 75 mg/day for adult women). What helps iron absorption is eating vitamin C in the same meal as iron from plant foods, so the daily report checks each meal and suggests when to add some. Heavy bleeding still needs clinical assessment.",
        "nutrients": {
            "Iron": "Menstrual bleeding increases iron losses, so the target uses the menstrual reference when that is higher than the usual age and sex value.",
            "Vitamin C": "Vitamin C in the same meal helps the body absorb iron from plant foods such as beans, lentils, spinach and fortified cereals. Its daily target stays the same; the meal check shows where to add it.",
        },
    },
}


def apply_menstruation_targets(targets, age):
    """Raise iron to the menstrual reference (NIH ODS) when that is higher.

    Vitamin C is deliberately left at its usual target: no reference raises it
    for menstruation. Its benefit for iron comes from eating it in the same meal,
    which services/iron_absorption.py checks per meal.
    """
    if age < 14:
        return targets
    iron = 15 if age <= 18 else 18
    for target in targets:
        if target["name"] == "Iron":
            target["target"] = max(target["target"], iron)
    return targets


def condition_micronutrient_guidance(conditions):
    return [profile for condition, profile in CONDITION_MICRONUTRIENTS.items()
            if condition in (conditions or [])]


PREGNANCY_TARGETS = {
    "Vitamin A": (750, 770, 770),
    "Thiamin (B1)": (1.4, 1.4, 1.4),
    "Riboflavin (B2)": (1.4, 1.4, 1.4),
    "Niacin (B3)": (18, 18, 18),
    "Pantothenic acid (B5)": (6, 6, 6),
    "Vitamin B6": (1.9, 1.9, 1.9),
    "Folate (B9)": (600, 600, 600),
    "Vitamin C": (80, 85, 85),
    "Vitamin D": (15, 15, 15),
    "Vitamin E": (15, 15, 15),
    "Vitamin K": (75, 90, 90),
    "Vitamin B12": (2.6, 2.6, 2.6),
    "Choline": (450, 450, 450),
    "Calcium": (1300, 1000, 1000),
    "Copper": (1, 1, 1),
    "Iron": (27, 27, 27),
    "Magnesium": (400, 350, 360),
    "Manganese": (2, 2, 2),
    "Phosphorus": (1250, 700, 700),
    "Potassium": (2600, 2900, 2900),
    "Selenium": (60, 60, 60),
    "Zinc": (12, 11, 11),
}


# Not tracked: few foods in USDA or on labels report them, so the bars would sit
# at 0 and mislead. Saved overrides for them are ignored.
UNTRACKED = {"Biotin (B7)", "Chloride", "Chromium", "Fluoride", "Iodine", "Molybdenum"}


def micronutrient_targets(age, sex, pregnant=False):
    if age < 1 or sex not in ("male", "female"):
        raise ValueError("Enter an age of at least 1 and select male or female.")
    if pregnant and not 14 <= age <= 50:
        raise ValueError("Pregnancy reference targets are available for ages 14 to 50.")

    band = next((index for index, upper in enumerate(AGE_BAND_ENDS) if age <= upper), len(AGE_BAND_ENDS))
    sex_index = 0 if sex == "male" else 1
    targets = [
        {"name": name, "unit": unit, "target": amounts[band][sex_index],
         "source": source,
         "direction": "maximum" if name == "Sodium" else "minimum"}
        for name, unit, _fda_dv, amounts, source in MICRONUTRIENTS
    ]
    if pregnant:
        pregnancy_band = 0 if age <= 18 else 1 if age <= 30 else 2
        for target in targets:
            if target["name"] in PREGNANCY_TARGETS:
                target["target"] = PREGNANCY_TARGETS[target["name"]][pregnancy_band]
                target["source"] = PREGNANCY_SOURCE
    return targets
