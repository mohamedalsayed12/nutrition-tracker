AGE_BAND_ENDS = (3, 8, 13, 18, 30, 50, 70)

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
    # Practical tracking targets for menaquinones (K2). NIH/EFSA do not set a separate K2 DRI;
    # adult values follow common clinical tracking guidance around 90 mcg/day.
    ("Vitamin K2", "mcg", 90, ((15, 15), (25, 25), (40, 40), (60, 60), (90, 90), (90, 90), (90, 90), (90, 90)), "https://ods.od.nih.gov/factsheets/VitaminK-HealthProfessional/"),
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


PREGNANCY_SOURCE = "https://ods.od.nih.gov/factsheets/Pregnancy-HealthProfessional/"
LACTATION_SOURCE = "https://ods.od.nih.gov/factsheets/Pregnancy-HealthProfessional/"

# Female-only reproductive conditions.
FEMALE_ONLY_CONDITIONS = frozenset({"pregnancy", "lactation", "menstruation", "menopause"})

# Conditions the API / UI accept. Keys must match CONDITION_MICRONUTRIENTS.
HEALTH_CONDITION_IDS = (
    "pregnancy",
    "lactation",
    "menstruation",
    "menopause",
    "diabetes",
    "ibs",
    "celiac",
    "crohn_ibd",
    "vegan",
    "vegetarian",
    "anemia_iron",
    "osteoporosis",
    "hypertension",
    "kidney_disease",
    "bariatric",
    "thyroid",
)

CONDITION_MICRONUTRIENTS = {
    "pregnancy": {
        "label": "Pregnancy",
        "source": PREGNANCY_SOURCE,
        "summary": "Pregnancy DRI targets replace age/sex defaults for key micronutrients. Review prenatal nutrition with your care team.",
        "nutrients": {
            "Folate (B9)": "Pregnancy reference is 600 mcg DFE/day.",
            "Iron": "Pregnancy reference is 27 mg/day.",
            "Iodine": "Pregnancy reference is 220 mcg/day.",
            "Choline": "Pregnancy reference is 450 mg/day.",
            "Calcium": "Pregnancy uses 1,300 mg/day (14–18) or 1,000 mg/day (adults).",
            "Vitamin B12": "Pregnancy reference is 2.6 mcg/day.",
        },
    },
    "lactation": {
        "label": "Lactation / breastfeeding",
        "source": LACTATION_SOURCE,
        "summary": "Lactation DRI targets replace age/sex defaults. Iron needs fall while iodine, vitamin A, and several B vitamins rise.",
        "nutrients": {
            "Vitamin A": "Lactation reference is higher to support milk composition.",
            "Iodine": "Lactation reference is 290 mcg/day.",
            "Iron": "Lactation iron reference is lower than pregnancy (about 9–10 mg/day for adults).",
            "Vitamin C": "Lactation reference is higher than non-lactating adults.",
            "Vitamin B12": "Lactation reference is 2.8 mcg/day.",
            "Choline": "Lactation reference is 550 mg/day.",
        },
    },
    "menstruation": {
        "label": "Period",
        "source": "https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/",
        "summary": "Raises iron and vitamin C targets while period is selected to highlight intake during bleeding and support nonheme iron absorption.",
        "nutrients": {
            "Iron": "Iron target rises by 5 mg above your age/sex reference.",
            "Vitamin C": "Vitamin C target rises by 35 mg to support iron absorption.",
        },
    },
    "menopause": {
        "label": "Menopause",
        "source": "https://ods.od.nih.gov/factsheets/Calcium-HealthProfessional/",
        "summary": "Emphasizes bone-supporting nutrients after menopause. Calcium and vitamin D rise when not already at the higher older-adult band.",
        "nutrients": {
            "Calcium": "Target rises toward 1,200 mg/day when below that level.",
            "Vitamin D": "Target rises toward 20 mcg/day when below that level.",
            "Magnesium": "Modest bump to support bone and muscle health.",
            "Vitamin K2": "Modest bump for bone-related tracking.",
        },
    },
    "diabetes": {
        "label": "Diabetes",
        "source": "https://diabetesjournals.org/care/article/49/Supplement_1/S50/163924/3-Prevention-or-Delay-of-Diabetes-and-Associated",
        "summary": "Raises vitamin B12 tracking for metformin-related risk and tightens the sodium limit. Discuss labs with your clinician.",
        "nutrients": {
            "Vitamin B12": "Target rises by 0.6 mcg to emphasize B12-rich intake.",
            "Sodium": "Daily sodium limit tightens to 1,500 mg.",
            "Chromium": "Modest bump for tracking; food logs cannot confirm glycemic benefit.",
            "Magnesium": "Modest bump; low magnesium is common with diabetes.",
        },
    },
    "ibs": {
        "label": "IBS",
        "source": "https://www.monashfodmap.com/blog/research-update-occurrence-micronutrient-deficiencies-ibs/",
        "summary": "Restrictive IBS diets often under-deliver calcium, iron, folate, thiamin, riboflavin, and magnesium; targets rise modestly to flag gaps.",
        "nutrients": {
            "Calcium": "Target rises by 100 mg.",
            "Iron": "Target rises by 2 mg.",
            "Folate (B9)": "Target rises by 50 mcg DFE.",
            "Thiamin (B1)": "Target rises by 0.2 mg.",
            "Riboflavin (B2)": "Target rises by 0.2 mg.",
            "Magnesium": "Target rises by 40 mg.",
        },
    },
    "celiac": {
        "label": "Celiac disease",
        "source": "https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/",
        "summary": "Untreated or newly diagnosed celiac disease is linked to iron, calcium, folate, B12, vitamin D, and zinc shortfalls; targets rise to highlight them.",
        "nutrients": {
            "Iron": "Target rises by 4 mg.",
            "Calcium": "Target rises by 200 mg.",
            "Folate (B9)": "Target rises by 100 mcg DFE.",
            "Vitamin B12": "Target rises by 0.6 mcg.",
            "Vitamin D": "Target rises by 5 mcg.",
            "Zinc": "Target rises by 2 mg.",
        },
    },
    "crohn_ibd": {
        "label": "Crohn’s / IBD",
        "source": "https://ods.od.nih.gov/factsheets/VitaminB12-HealthProfessional/",
        "summary": "Inflammatory bowel disease commonly affects B12, iron, vitamin D, calcium, zinc, and folate status; targets rise to flag higher needs.",
        "nutrients": {
            "Vitamin B12": "Target rises by 1.0 mcg.",
            "Iron": "Target rises by 4 mg.",
            "Vitamin D": "Target rises by 10 mcg.",
            "Calcium": "Target rises by 200 mg.",
            "Zinc": "Target rises by 3 mg.",
            "Folate (B9)": "Target rises by 100 mcg DFE.",
        },
    },
    "vegan": {
        "label": "Vegan",
        "source": "https://ods.od.nih.gov/factsheets/VitaminB12-HealthProfessional/",
        "summary": "Strict vegan diets need reliable B12 and careful iron, zinc, calcium, iodine, and vitamin D planning; targets rise accordingly.",
        "nutrients": {
            "Vitamin B12": "Target rises by 2.0 mcg (fortified foods or a supplement are typically required).",
            "Iron": "Target rises by 8 mg to offset lower nonheme absorption.",
            "Zinc": "Target rises by 3 mg.",
            "Calcium": "Target rises by 200 mg.",
            "Iodine": "Target rises by 50 mcg.",
            "Vitamin D": "Target rises by 5 mcg.",
        },
    },
    "vegetarian": {
        "label": "Vegetarian",
        "source": "https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/",
        "summary": "Lacto-ovo vegetarian patterns can still under-deliver iron, zinc, and B12; targets rise modestly (vegan adjustments replace these if both are selected).",
        "nutrients": {
            "Iron": "Target rises by 4 mg.",
            "Zinc": "Target rises by 2 mg.",
            "Vitamin B12": "Target rises by 0.6 mcg.",
        },
    },
    "anemia_iron": {
        "label": "Iron-deficiency anemia",
        "source": "https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/",
        "summary": "Raises iron and vitamin C targets. Food tracking cannot replace clinical treatment; follow your clinician’s plan.",
        "nutrients": {
            "Iron": "Target rises by 10 mg.",
            "Vitamin C": "Target rises by 50 mg to support nonheme iron absorption.",
            "Folate (B9)": "Target rises by 100 mcg DFE.",
            "Vitamin B12": "Target rises by 0.6 mcg.",
        },
    },
    "osteoporosis": {
        "label": "Osteoporosis / bone loss",
        "source": "https://ods.od.nih.gov/factsheets/Calcium-HealthProfessional/",
        "summary": "Raises calcium, vitamin D, magnesium, and vitamin K2 tracking targets for bone support.",
        "nutrients": {
            "Calcium": "Target rises toward at least 1,200 mg/day.",
            "Vitamin D": "Target rises toward at least 20 mcg/day.",
            "Magnesium": "Target rises by 50 mg.",
            "Vitamin K2": "Target rises by 30 mcg.",
            "Vitamin K": "Target rises by 20 mcg.",
        },
    },
    "hypertension": {
        "label": "Hypertension",
        "source": "https://ods.od.nih.gov/factsheets/Sodium-Consumer/",
        "summary": "Tightens the sodium limit and raises potassium tracking, consistent with DASH-style guidance.",
        "nutrients": {
            "Sodium": "Daily sodium limit tightens to 1,500 mg.",
            "Potassium": "Target rises by 500 mg when below 3,400 mg.",
            "Magnesium": "Target rises by 40 mg.",
            "Calcium": "Target rises by 100 mg.",
        },
    },
    "kidney_disease": {
        "label": "Chronic kidney disease",
        "source": "https://www.kidney.org/atoz/content/nutrikidfail_stage1-4",
        "summary": "Lowers potassium, phosphorus, and sodium limits. Individual renal diets vary—use clinician/dietitian targets when they differ.",
        "nutrients": {
            "Potassium": "Upper tracking limit set to 2,000 mg.",
            "Phosphorus": "Upper tracking limit set to 800 mg.",
            "Sodium": "Daily sodium limit tightens to 1,500 mg.",
        },
    },
    "bariatric": {
        "label": "Bariatric surgery",
        "source": "https://ods.od.nih.gov/factsheets/VitaminB12-HealthProfessional/",
        "summary": "Post-bariatric absorption changes raise B12, iron, calcium, vitamin D, and thiamin tracking targets.",
        "nutrients": {
            "Vitamin B12": "Target rises by 2.5 mcg.",
            "Iron": "Target rises by 8 mg.",
            "Calcium": "Target rises by 300 mg.",
            "Vitamin D": "Target rises by 15 mcg.",
            "Thiamin (B1)": "Target rises by 0.5 mg.",
            "Folate (B9)": "Target rises by 100 mcg DFE.",
            "Zinc": "Target rises by 3 mg.",
        },
    },
    "thyroid": {
        "label": "Thyroid disorder",
        "source": "https://ods.od.nih.gov/factsheets/Iodine-HealthProfessional/",
        "summary": "Raises iodine and selenium tracking. Excess iodine can worsen some thyroid conditions—confirm with your clinician.",
        "nutrients": {
            "Iodine": "Target rises by 50 mcg.",
            "Selenium": "Target rises by 10 mcg.",
            "Iron": "Target rises by 2 mg (iron status can interact with thyroid function).",
            "Zinc": "Target rises by 2 mg.",
        },
    },
}


# Additive / cap adjustments applied after pregnancy/lactation base targets.
# Keys: add (raise minimum), floor (raise to at least), set_max (lower maximum / set limit).
CONDITION_TARGET_ADJUSTMENTS = {
    "menstruation": {
        "Iron": {"add": 5.0, "source": "https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/"},
        "Vitamin C": {"add": 35.0, "source": "https://ods.od.nih.gov/factsheets/VitaminC-Consumer/"},
    },
    "menopause": {
        "Calcium": {"floor": 1200.0},
        "Vitamin D": {"floor": 20.0},
        "Magnesium": {"add": 40.0},
        "Vitamin K2": {"add": 30.0},
    },
    "diabetes": {
        "Vitamin B12": {"add": 0.6},
        "Sodium": {"set_max": 1500.0},
        "Chromium": {"add": 5.0},
        "Magnesium": {"add": 40.0},
    },
    "ibs": {
        "Calcium": {"add": 100.0},
        "Iron": {"add": 2.0},
        "Folate (B9)": {"add": 50.0},
        "Thiamin (B1)": {"add": 0.2},
        "Riboflavin (B2)": {"add": 0.2},
        "Magnesium": {"add": 40.0},
    },
    "celiac": {
        "Iron": {"add": 4.0},
        "Calcium": {"add": 200.0},
        "Folate (B9)": {"add": 100.0},
        "Vitamin B12": {"add": 0.6},
        "Vitamin D": {"add": 5.0},
        "Zinc": {"add": 2.0},
    },
    "crohn_ibd": {
        "Vitamin B12": {"add": 1.0},
        "Iron": {"add": 4.0},
        "Vitamin D": {"add": 10.0},
        "Calcium": {"add": 200.0},
        "Zinc": {"add": 3.0},
        "Folate (B9)": {"add": 100.0},
    },
    "vegan": {
        "Vitamin B12": {"add": 2.0},
        "Iron": {"add": 8.0},
        "Zinc": {"add": 3.0},
        "Calcium": {"add": 200.0},
        "Iodine": {"add": 50.0},
        "Vitamin D": {"add": 5.0},
    },
    "vegetarian": {
        "Iron": {"add": 4.0},
        "Zinc": {"add": 2.0},
        "Vitamin B12": {"add": 0.6},
    },
    "anemia_iron": {
        "Iron": {"add": 10.0},
        "Vitamin C": {"add": 50.0},
        "Folate (B9)": {"add": 100.0},
        "Vitamin B12": {"add": 0.6},
    },
    "osteoporosis": {
        "Calcium": {"floor": 1200.0},
        "Vitamin D": {"floor": 20.0},
        "Magnesium": {"add": 50.0},
        "Vitamin K2": {"add": 30.0},
        "Vitamin K": {"add": 20.0},
    },
    "hypertension": {
        "Sodium": {"set_max": 1500.0},
        "Potassium": {"add": 500.0},
        "Magnesium": {"add": 40.0},
        "Calcium": {"add": 100.0},
    },
    "kidney_disease": {
        "Potassium": {"set_max": 2000.0},
        "Phosphorus": {"set_max": 800.0},
        "Sodium": {"set_max": 1500.0},
    },
    "bariatric": {
        "Vitamin B12": {"add": 2.5},
        "Iron": {"add": 8.0},
        "Calcium": {"add": 300.0},
        "Vitamin D": {"add": 15.0},
        "Thiamin (B1)": {"add": 0.5},
        "Folate (B9)": {"add": 100.0},
        "Zinc": {"add": 3.0},
    },
    "thyroid": {
        "Iodine": {"add": 50.0},
        "Selenium": {"add": 10.0},
        "Iron": {"add": 2.0},
        "Zinc": {"add": 2.0},
    },
}


def condition_micronutrient_guidance(conditions):
    return [dict(condition=condition, **profile)
            for condition, profile in CONDITION_MICRONUTRIENTS.items()
            if condition in (conditions or [])]


def _apply_change(row, condition, change):
    if row.get("custom"):
        return False
    current = float(row["target"])
    changed = False
    if "add" in change:
        row["target"] = round(current + float(change["add"]), 1)
        changed = True
    if "floor" in change:
        floor = float(change["floor"])
        if current < floor or ("add" in change and float(row["target"]) < floor):
            row["target"] = round(max(float(row["target"]), floor), 1)
            changed = True
    if "set_max" in change:
        row["target"] = round(float(change["set_max"]), 1)
        row["direction"] = "maximum"
        changed = True
    if not changed:
        return False
    row["condition_adjusted"] = True
    row["adjusted_by"] = sorted(set(row.get("adjusted_by") or []) | {condition})
    if change.get("source"):
        row["source"] = change["source"]
    return True


def apply_condition_target_adjustments(targets, conditions):
    """Apply additive / floor / max adjustments for active medical conditions.

    Pregnancy and lactation absolute DRIs are applied earlier in micronutrient_targets.
    Personal overrides (custom=True) are left unchanged.
    Vegan adjustments replace vegetarian when both are selected.
    """
    active = [condition for condition in HEALTH_CONDITION_IDS if condition in set(conditions or [])]
    if "vegan" in active and "vegetarian" in active:
        active = [condition for condition in active if condition != "vegetarian"]
    if not active:
        return targets

    adjusted = [dict(target) for target in targets]
    by_name = {row["name"]: row for row in adjusted}
    for condition in active:
        changes = CONDITION_TARGET_ADJUSTMENTS.get(condition) or {}
        for nutrient, change in changes.items():
            row = by_name.get(nutrient)
            if row is not None:
                _apply_change(row, condition, change)
    return adjusted


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
    "Vitamin K2": (90, 90, 90),
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

# Age bands: <=18, 19–30, 31+ (female lactation DRIs).
LACTATION_TARGETS = {
    "Vitamin A": (1200, 1300, 1300),
    "Thiamin (B1)": (1.4, 1.4, 1.4),
    "Riboflavin (B2)": (1.6, 1.6, 1.6),
    "Niacin (B3)": (17, 17, 17),
    "Pantothenic acid (B5)": (7, 7, 7),
    "Vitamin B6": (2.0, 2.0, 2.0),
    "Biotin (B7)": (35, 35, 35),
    "Folate (B9)": (500, 500, 500),
    "Vitamin C": (115, 120, 120),
    "Vitamin D": (15, 15, 15),
    "Vitamin E": (19, 19, 19),
    "Vitamin K": (75, 90, 90),
    "Vitamin K2": (90, 90, 90),
    "Vitamin B12": (2.8, 2.8, 2.8),
    "Choline": (550, 550, 550),
    "Calcium": (1300, 1000, 1000),
    "Chloride": (2300, 2300, 2300),
    "Chromium": (44, 45, 45),
    "Copper": (1.3, 1.3, 1.3),
    "Fluoride": (3, 3, 3),
    "Iodine": (290, 290, 290),
    "Iron": (10, 9, 9),
    "Magnesium": (360, 310, 320),
    "Manganese": (2.6, 2.6, 2.6),
    "Molybdenum": (50, 50, 50),
    "Phosphorus": (1250, 700, 700),
    "Potassium": (2500, 2800, 2800),
    "Selenium": (70, 70, 70),
    "Zinc": (13, 12, 12),
}


def micronutrient_targets(age, sex, pregnant=False, lactating=False):
    if age < 1 or sex not in ("male", "female"):
        raise ValueError("Enter an age of at least 1 and select male or female.")
    if pregnant and lactating:
        raise ValueError("Choose pregnancy or lactation, not both.")
    if pregnant and not 14 <= age <= 50:
        raise ValueError("Pregnancy reference targets are available for ages 14 to 50.")
    if lactating and not 14 <= age <= 50:
        raise ValueError("Lactation reference targets are available for ages 14 to 50.")

    band = next((index for index, upper in enumerate(AGE_BAND_ENDS) if age <= upper), len(AGE_BAND_ENDS))
    sex_index = 0 if sex == "male" else 1
    targets = [
        {"name": name, "unit": unit, "target": amounts[band][sex_index],
         "source": source,
         "direction": "maximum" if name == "Sodium" else "minimum"}
        for name, unit, _fda_dv, amounts, source in MICRONUTRIENTS
    ]

    life_band = 0 if age <= 18 else 1 if age <= 30 else 2
    if pregnant:
        for target in targets:
            if target["name"] in PREGNANCY_TARGETS:
                target["target"] = PREGNANCY_TARGETS[target["name"]][life_band]
                target["source"] = PREGNANCY_SOURCE
    elif lactating:
        for target in targets:
            if target["name"] in LACTATION_TARGETS:
                target["target"] = LACTATION_TARGETS[target["name"]][life_band]
                target["source"] = LACTATION_SOURCE
    return targets
