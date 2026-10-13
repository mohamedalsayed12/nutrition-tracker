# Nutrition Tracker

A Flask app for recording meals and activity, estimating calorie targets, and viewing nutrition targets.

## Code layout

- `imports.py` gathers standard-library, installed-package, and app route imports; project names are resolved when requested to avoid circular imports.
- `db.py` owns database setup, stored-record access, the complete USDA search index, and the API search cache.
- `api.py` contains the USDA and API Ninjas integrations and search endpoints.
- `build_food_index.py` streams a USDA CSV download into the local food search index.
- `models.py` defines the database tables.
- `auth.py` contains registration, login, and user loading.
- `app.py` contains the tracker routes and request handling.
- `calc.py` contains nutrition, exercise, and target calculations.

## Local setup

1. Create and activate a Python virtual environment.
2. Install the packages with `python -m pip install -r requirements.txt`.
3. Create a `.env` file with `FDC_API_KEY`, `API_NINJAS_KEY`, and a persistent `SECRET_KEY`. `API_NINJAS_KEY` is needed for exercise name suggestions.
4. Download the latest **Full Download of All Data Types (CSV)** ZIP from the [USDA FoodData Central downloads page](https://fdc.nal.usda.gov/download-datasets/). Build the local search index with `python build_food_index.py "path/to/FoodData_Central_csv_YYYY-MM-DD.zip"`. This streams the archive and creates `instance/food_index.sqlite3`; it does not extract the full archive. Stop the web app while rebuilding the index. Run the same command with a newer USDA ZIP to refresh it.
5. Start the web app with `python -m flask --app app run --debug`.
6. Open `http://127.0.0.1:5000/register` to create an account, or `http://127.0.0.1:5000/login` to sign in.

On the homepage, search all indexed USDA foods by name, word fragments (for example, `soup car`), FDC ID, or exact barcode. The single result list includes generic and branded foods and prioritizes foods you have logged before; Tab or Enter selects the top result. If the index has not been built, search falls back to the live USDA API. Selecting a food and logging its nutrients still requires `FDC_API_KEY` because those details come from the USDA API. Enter a quantity using an available USDA serving size (such as one egg, cup, or slice) or a weight unit (grams, 100 grams, ounces, pounds, or kilograms). When a USDA portion gives a food-specific volume weight, the app also estimates cups, fluid ounces, tablespoons, teaspoons, milliliters, and 100 milliliters from that portion. Logged nutrients are calculated from the resulting gram weight.

Each meal also shows up to five of the signed-in user's most logged foods. Selecting one fills its last logged gram amount; the user can change that amount and save it again. These choices come from existing food logs, so logging or deleting a food updates them without a separate cache to maintain.

## Medical condition setting

Selecting diabetes or IBS adds source-linked nutrition guidance and condition context to the homepage. It does not impose an automatic macro split: the [2026 ADA Standards](https://diabetesjournals.org/care/article/49/Supplement_1/S89/163932) call for individualized diabetes targets, while [NIDDK IBS guidance](https://www.niddk.nih.gov/health-information/digestive-diseases/irritable-bowel-syndrome/eating-diet-nutrition) focuses on symptom-specific food choices, soluble fiber, and low-FODMAP trials. The setting lets the user enter personal daily carbohydrate, protein, and fat amounts in grams. Entered amounts replace the corresponding calculator or macro-split targets; the remaining calorie budget is divided across macros without gram overrides. Targets whose energy exceeds the calorie goal are rejected.

For diabetes, the homepage shows reported dietary fiber against the ADA reference of 14 g per 1,000 kcal. For IBS, it shows reported total dietary fiber but does not infer soluble fiber or FODMAP content from USDA data.

Pregnancy, diabetes, IBS, and periods / menstruation also add source-linked focus notes to the existing micronutrient progress bars:

- Pregnancy uses [NIH pregnancy reference amounts](https://ods.od.nih.gov/factsheets/Pregnancy-HealthProfessional/), highlighting folate, iron, iodine, choline, vitamin D, and calcium.
- Diabetes highlights B12 monitoring **if taking metformin long term**, following [ADA guidance](https://diabetesjournals.org/care/article/49/Supplement_1/S50/163924/3-Prevention-or-Delay-of-Diabetes-and-Associated). This does not automatically increase B12 targets.
- IBS highlights calcium, iron, folate, thiamin, riboflavin, and magnesium adequacy when diets are restricted, based on [Monash guidance](https://www.monashfodmap.com/blog/research-update-occurrence-micronutrient-deficiencies-ibs/). Usual reference amounts remain in place.
- Periods / menstruation highlights iron and vitamin C using [NIH guidance](https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/). Existing age/sex iron references remain in place; no extra cycle-phase increase is applied. A user whose reference does not match their menstrual status can enter a clinician-set target. Pregnancy and menstruation cannot be selected together.

Personal micronutrient overrides take priority. Focus notes explain dietary considerations; logged intake cannot diagnose deficiencies or determine supplement doses. Missing USDA nutrient amounts remain unknown or partial in the progress display.

Local environment files and SQLite databases are excluded from Git. The index searches every food record in the downloaded release, but it stores only search metadata; nutrient and serving details are fetched for selected foods.
