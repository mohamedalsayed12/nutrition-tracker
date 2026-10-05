"""Published daily micronutrient reference amounts for nonpregnant people.

Age/sex intakes: NIH and Health Canada reference tables linked below.
"""

AGE_BAND_ENDS = (3, 8, 13, 18, 30, 50, 70)

# Each age-band value is (male, female), from ages 1-3 through 71+.
##List the 29 tracked micronutrients with personal age/sex values.
##Sodium uses a daily limit.
MICRONUTRIENTS = (
    ("Vitamin A", "mcg RAE", 900, ((300, 300), (400, 400), (600, 600), (900, 700), (900, 700), (900, 700), (900, 700), (900, 700)), "https://ods.od.nih.gov/factsheets/VitaminA-Consumer/"),
    ("Thiamin (B1)", "mg", 1.2, ((0.5, 0.5), (0.6, 0.6), (0.9, 0.9), (1.2, 1.0), (1.2, 1.1), (1.2, 1.1), (1.2, 1.1), (1.2, 1.1)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Riboflavin (B2)", "mg", 1.3, ((0.5, 0.5), (0.6, 0.6), (0.9, 0.9), (1.3, 1.0), (1.3, 1.1), (1.3, 1.1), (1.3, 1.1), (1.3, 1.1)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Niacin (B3)", "mg NE", 16, ((6, 6), (8, 8), (12, 12), (16, 14), (16, 14), (16, 14), (16, 14), (16, 14)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Pantothenic acid (B5)", "mg", 5, ((2, 2), (3, 3), (4, 4), (5, 5), (5, 5), (5, 5), (5, 5), (5, 5)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Vitamin B6", "mg", 1.7, ((0.5, 0.5), (0.6, 0.6), (1, 1), (1.3, 1.2), (1.3, 1.3), (1.3, 1.3), (1.7, 1.5), (1.7, 1.5)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Biotin (B7)", "mcg", 30, ((8, 8), (12, 12), (20, 20), (25, 25), (30, 30), (30, 30), (30, 30), (30, 30)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Folate (B9)", "mcg DFE", 400, ((150, 150), (200, 200), (300, 300), (400, 400), (400, 400), (400, 400), (400, 400), (400, 400)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Vitamin C", "mg", 90, ((15, 15), (25, 25), (45, 45), (75, 65), (90, 75), (90, 75), (90, 75), (90, 75)), "https://ods.od.nih.gov/factsheets/VitaminC-Consumer/"),
    ("Vitamin D", "mcg", 20, ((15, 15), (15, 15), (15, 15), (15, 15), (15, 15), (15, 15), (15, 15), (20, 20)), "https://ods.od.nih.gov/factsheets/VitaminD-Consumer/"),
    ("Vitamin E", "mg", 15, ((6, 6), (7, 7), (11, 11), (15, 15), (15, 15), (15, 15), (15, 15), (15, 15)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Vitamin K", "mcg", 120, ((30, 30), (55, 55), (60, 60), (75, 75), (120, 90), (120, 90), (120, 90), (120, 90)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Vitamin B12", "mcg", 2.4, ((0.9, 0.9), (1.2, 1.2), (1.8, 1.8), (2.4, 2.4), (2.4, 2.4), (2.4, 2.4), (2.4, 2.4), (2.4, 2.4)), "https://ods.od.nih.gov/factsheets/VitaminB12-Consumer/"),
    ("Choline", "mg", 550, ((200, 200), (250, 250), (375, 375), (550, 400), (550, 425), (550, 425), (550, 425), (550, 425)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-vitamins.html"),
    ("Calcium", "mg", 1300, ((700, 700), (1000, 1000), (1300, 1300), (1300, 1300), (1000, 1000), (1000, 1000), (1000, 1200), (1200, 1200)), "https://ods.od.nih.gov/factsheets/Calcium-HealthProfessional/"),
    ("Chloride", "mg", 2300, ((1500, 1500), (1900, 1900), (2300, 2300), (2300, 2300), (2300, 2300), (2300, 2300), (2000, 2000), (1800, 1800)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Chromium", "mcg", 35, ((11, 11), (15, 15), (25, 21), (35, 24), (35, 25), (35, 25), (30, 20), (30, 20)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Copper", "mg", 0.9, ((0.34, 0.34), (0.44, 0.44), (0.7, 0.7), (0.89, 0.89), (0.9, 0.9), (0.9, 0.9), (0.9, 0.9), (0.9, 0.9)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Fluoride", "mg", None, ((0.7, 0.7), (1, 1), (2, 2), (3, 3), (4, 3), (4, 3), (4, 3), (4, 3)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Iodine", "mcg", 150, ((90, 90), (90, 90), (120, 120), (150, 150), (150, 150), (150, 150), (150, 150), (150, 150)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Iron", "mg", 18, ((7, 7), (10, 10), (8, 8), (11, 15), (8, 18), (8, 18), (8, 8), (8, 8)), "https://ods.od.nih.gov/factsheets/Iron-Consumer/"),
    ("Magnesium", "mg", 420, ((80, 80), (130, 130), (240, 240), (410, 360), (400, 310), (420, 320), (420, 320), (420, 320)), "https://ods.od.nih.gov/factsheets/Magnesium-HealthProfessional/"),
    ("Manganese", "mg", 2.3, ((1.2, 1.2), (1.5, 1.5), (1.9, 1.6), (2.2, 1.6), (2.3, 1.8), (2.3, 1.8), (2.3, 1.8), (2.3, 1.8)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Molybdenum", "mcg", 45, ((17, 17), (22, 22), (34, 34), (43, 43), (45, 45), (45, 45), (45, 45), (45, 45)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Phosphorus", "mg", 1250, ((460, 460), (500, 500), (1250, 1250), (1250, 1250), (700, 700), (700, 700), (700, 700), (700, 700)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Potassium", "mg", 4700, ((2000, 2000), (2300, 2300), (2500, 2300), (3000, 2300), (3400, 2600), (3400, 2600), (3400, 2600), (3400, 2600)), "https://ods.od.nih.gov/factsheets/Potassium-Consumer/"),
    ("Selenium", "mcg", 55, ((20, 20), (30, 30), (40, 40), (55, 55), (55, 55), (55, 55), (55, 55), (55, 55)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Sodium", "mg", 2300, ((1200, 1200), (1500, 1500), (1800, 1800), (2300, 2300), (2300, 2300), (2300, 2300), (2300, 2300), (2300, 2300)), "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-elements.html"),
    ("Zinc", "mg", 11, ((3, 3), (5, 5), (8, 8), (11, 9), (11, 8), (11, 8), (11, 8), (11, 8)), "https://ods.od.nih.gov/factsheets/Zinc-Consumer/"),
)


##Pregnancy values are NIH ODS RDAs/AIs for ages 14-18, 19-30, and 31-50.
PREGNANCY_SOURCE = "https://ods.od.nih.gov/factsheets/Pregnancy-HealthProfessional/"
PREGNANCY_TARGETS = {
    "Vitamin A": (750, 770, 770),
    "Thiamin (B1)": (1.4, 1.4, 1.4),
    "Riboflavin (B2)": (1.4, 1.4, 1.4),
    "Niacin (B3)": (18, 18, 18),
    "Pantothenic acid (B5)": (6, 6, 6),
    "Vitamin B6": (1.9, 1.9, 1.9),
    "Biotin (B7)": (30, 30, 30),
    "Folate (B9)": (600, 600, 600),
    "Vitamin C": (80, 85, 85),
    "Vitamin D": (15, 15, 15),
    "Vitamin E": (15, 15, 15),
    "Vitamin K": (75, 90, 90),
    "Vitamin B12": (2.6, 2.6, 2.6),
    "Choline": (450, 450, 450),
    "Calcium": (1300, 1000, 1000),
    "Chloride": (2300, 2300, 2300),
    "Chromium": (29, 30, 30),
    "Copper": (1, 1, 1),
    "Fluoride": (3, 3, 3),
    "Iodine": (220, 220, 220),
    "Iron": (27, 27, 27),
    "Magnesium": (400, 350, 360),
    "Manganese": (2, 2, 2),
    "Molybdenum": (50, 50, 50),
    "Phosphorus": (1250, 700, 700),
    "Potassium": (2600, 2900, 2900),
    "Selenium": (60, 60, 60),
    "Zinc": (12, 11, 11),
}


##Choose the right age band, sex, and pregnancy reference values.
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
