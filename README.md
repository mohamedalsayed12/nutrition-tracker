# Nutrition Tracker API

A Flask REST backend for user accounts, food and activity logs, nutrition targets, health preferences, and reports. PostgreSQL stores application records through SQLAlchemy. The project contains no HTML templates, browser pages, or form/session authentication.

## Architecture

The layout follows the social media FastAPI project's separation of responsibilities, using Flask Blueprints for routers.

| Module | Responsibility |
| --- | --- |
| `main.py` | Application factory and extension initialization. |
| `app.py` | WSGI entry point for Vercel and a factory import for Flask tools. |
| `config.py` | Environment settings and PostgreSQL connection URL. |
| `database.py` | SQLAlchemy ORM, database initialization, and Flask-Migrate. |
| `models.py` | Persistent user and nutrition models. |
| `schemas.py` | Pydantic request validation. |
| `oauth2.py` | JWT configuration and authenticated user lookup. |
| `auth.py` | JSON login and access token creation. |
| `utils.py` | Password hashing and verification. |
| `routers/` | HTTP routes for users, logs, goals, settings, foods, and reports. |
| `services/` | Nutrition calculations, external integrations, and application operations. |
| `migrations/` | Versioned Alembic migrations through Flask-Migrate. |
| `tests/conftest.py` | Isolated application, database, and authentication fixtures. |
| `.github/workflows/build-deploy.yml` | PostgreSQL tests, optional Docker publishing, and gated Vercel deployment. |

The request flow is: router → Pydantic schema → service → SQLAlchemy model → PostgreSQL. JWT authentication checks that the token's user still exists. Resource queries always include the signed-in user's ID.

## Run locally

From this project directory in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
docker compose up -d database
.\.venv\Scripts\python.exe -m flask --app main db upgrade
.\.venv\Scripts\python.exe -m flask --app main run --debug --port 8000
```

The database container exposes PostgreSQL on `127.0.0.1:5432` and persists its records in a named Docker volume. Add the settings from `.env.example` to your ignored local `.env`. `DATABASE_HOSTNAME` is `localhost` when Flask runs on Windows and `database` inside Compose. SQLAlchemy builds the connection URL from separate fields, including passwords containing special characters. `DATABASE_URL` may be supplied instead and takes precedence. PostgreSQL is required for the application and tests.

Use separate random values for `SECRET_KEY` and `JWT_SECRET_KEY`. `FDC_API_KEY` enables USDA food lookup and food logging. `API_NINJAS_KEY` enables exercise search. Set `FRONTEND_ORIGIN` to your future frontend's exact origin; multiple origins can be comma separated. Access tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES`, defaulting to 30.

To run both the API and PostgreSQL in containers:

```powershell
docker compose up -d --build
```

The API container applies migrations before starting Gunicorn on port 8000. `/api/v1/health` checks the application; `/api/v1/ready` checks the PostgreSQL connection.

## API contract

`GET /openapi.json` returns the OpenAPI specification and request schemas for frontend development. All application routes return JSON, including errors.

| Method and path | Purpose |
| --- | --- |
| `POST /api/v1/users` | Register with `name`, `email`, and `password`. |
| `GET /api/v1/users/me` | Read the authenticated user. |
| `POST /api/v1/auth/login` | Exchange email and password for an access token. |
| `GET`, `POST /api/v1/food-logs` | List or create your food logs. |
| `GET`, `PUT`, `DELETE /api/v1/food-logs/{id}` | Read, replace, or delete your food log. |
| `GET`, `POST /api/v1/activity-logs` | List or create your activity logs. |
| `GET`, `PUT`, `DELETE /api/v1/activity-logs/{id}` | Read, replace, or delete your activity log. |
| `GET`, `PUT /api/v1/goals/calories` | Read or set your calorie target. |
| `GET`, `PUT /api/v1/goals/nutrition` | Read or calculate nutrition targets. |
| `GET`, `PUT /api/v1/settings/health` | Read or replace health preferences and personal targets. |
| `GET`, `PUT`, `DELETE /api/v1/settings/macro-split` | Read, replace, or reset macro percentages. |
| `GET /api/v1/foods?q=...` | Search USDA foods, optionally personalized with a token. |
| `GET /api/v1/foods/{fdc_id}/measures` | Read serving size conversions. |
| `GET /api/v1/foods/frequent` | Read your frequently logged foods. |
| `GET /api/v1/exercises?q=...` | Search exercise names. |
| `GET /api/v1/reports/daily` | Read daily totals, targets, exercise credit, active day conditions, and food advice for nutrients below target. |
| `GET /api/v1/reports/weekly` | Read a seven day nutrition recap. |
| `GET /api/v1/nutrients/food-recommendations` | Read food suggestions for every tracked micronutrient, including vitamin K2. |
| `GET`, `PUT`, `DELETE /api/v1/days/{YYYY-MM-DD}/conditions` | Read, replace, or clear day-scoped conditions such as menstruation. |
| `PUT /api/v1/days/{YYYY-MM-DD}/save` | Save a logged UTC day. |
| `GET /api/v1/days` | Read saved UTC days. |

Protected routes require `Authorization: Bearer <access_token>`. Food and activity listings accept `page` and `per_page` (maximum 100). Daily reports accept `date=YYYY-MM-DD`; weekly reports accept `week_start=YYYY-MM-DD`. Reports accept an IANA `timezone`, such as `Europe/London`, and default to UTC. Saved days use UTC; changing or deleting food logs reopens their saved day.

Day-scoped conditions currently support `menstruation` (period days). Logging a period day raises that day's iron target by 5 mg and vitamin C by 35 mg above the age/sex reference. Personal micronutrient overrides marked custom are not auto-bumped. The same iron and vitamin C bumps apply when menstruation is enabled as an ongoing condition in `PUT /api/v1/settings/health`. Menstruation requires nutrition sex `female`. Pregnancy and menstruation cannot both be active. Daily reports include `day_conditions`, `active_conditions` (health settings merged with the day log), `condition_guidance`, `nutrient_advice` (foods to eat when a nutrient is below target), and `condition_adjusted` flags on raised micronutrient rows. Weekly reports use ongoing health-preference conditions only.

Micronutrient targets include vitamin K2 (menaquinones) with a practical adult tracking target of 90 mcg/day. NIH/EFSA do not publish a separate K2 DRI, so this value is a tracking goal for food logging rather than an official RDA. Each micronutrient row in the daily report also lists `food_recommendations`; when intake is below the minimum target (or above the sodium limit), `deficient` is true and `advice` names foods that help close the gap.

Day conditions use:

```json
{"conditions": ["menstruation"]}
```

Food log creation and replacement use:

```json
{"meal": "breakfast", "fdc_id": 123456, "grams": 50}
```

Nutrient amounts come from USDA on the server. Allowed meals are `breakfast`, `lunch`, `dinner`, and `snack`.

Nutrition setup uses:

```json
{"age": 30, "sex": "male", "height_cm": 175, "weight_kg": 75, "activity_level": "moderately active", "goal": "maintain"}
```

The existing calculation rules and source-linked condition guidance are retained as backend services. Activity logging requires nutrition setup. Use `/openapi.json` for complete field constraints and allowed values.

## Database migrations and existing records

Schema changes run explicitly through migrations; starting Flask does not create or alter tables.

```powershell
.\.venv\Scripts\python.exe -m flask --app main db migrate -m "Describe the schema change"
.\.venv\Scripts\python.exe -m flask --app main db upgrade
```

Review generated migrations before applying them. The initial revision supports the existing tracker schema, including its two historical health preference columns. The existing tracker records have been transferred to PostgreSQL. Food search and serving sizes use the USDA API and require `FDC_API_KEY`.

SQLAlchemy binds query values separately from SQL. User input is never interpolated into query strings.

## Tests and CI

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use a dedicated PostgreSQL database named `nutrition_test` by default, using the connection settings from `.env`. Create it once with `docker compose exec -T database createdb -U nutrition nutrition_test`. You can instead provide `TEST_DATABASE_URL` pointing to another dedicated database whose name ends in `_test`. Tests create and remove its application tables. Never use your application database as the test database. CI starts PostgreSQL 16, applies migrations, and runs the suite against its test database.

Docker publishing is optional: set the repository variable `PUBLISH_DOCKER_IMAGE=true` and production environment secrets `DOCKER_HUB_USERNAME` and `DOCKER_HUB_ACCESS_TOKEN`. Successful main branch builds then publish `<username>/nutrition-tracker:latest`.

## Vercel deployment

Vercel runs the Flask `app` exported from `app.py` with Python 3.14. The deployment job runs after the PostgreSQL test job succeeds, applies Alembic migrations to the hosted database, and deploys the application. Vercel's automatic Git deployment is disabled in `vercel.json` so the GitHub Actions test gate controls production deployment.

Connect a hosted PostgreSQL database to the Vercel project for the production environment. The Neon integration provides `DATABASE_URL` to the project. The local Docker database at `127.0.0.1` is not reachable from Vercel or GitHub Actions. The deployment job reads the production database URL through Vercel CLI when it runs migrations, so the database must allow connections from GitHub Actions as well.

Create a GitHub Actions environment named `deployment` and add these environment secrets:

| Secret | Purpose |
| --- | --- |
| `VERCEL_TOKEN` | Vercel API token used by the deployment job. |
| `VERCEL_ORG_ID` | Vercel account or team ID from the linked project's `.vercel/project.json`. |
| `VERCEL_PROJECT_ID` | Vercel project ID from the same file. |
| `SECRET_KEY` | Random Flask session signing key, separate from local development. |
| `JWT_SECRET_KEY` | Random JWT signing key, separate from the Flask key. |
| `FDC_API_KEY` | USDA FoodData Central API key for food search and logging. |
| `API_NINJAS_KEY` | API Ninjas key for exercise search, if used. |
| `FRONTEND_ORIGIN` | Allowed frontend origin for CORS, when a frontend is available. |

The workflow passes application settings to Vercel as deployment environment variables. `DATABASE_URL` stays in the Vercel integration rather than being duplicated in GitHub secrets. Once the database is connected to the project and the secrets are ready, set the repository variable `ENABLE_VERCEL_DEPLOY=true`. Pushes to `main` then deploy after tests pass. The job is skipped until that variable is set.

The Vercel CLI also ignores `.env`, `instance/`, and tests through `.vercelignore`. Do not commit production credentials.

## Framework references

- [Flask application factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/)
- [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/)
- [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/)
- [SQLAlchemy bound parameters](https://docs.sqlalchemy.org/en/20/tutorial/dbapi_transactions.html)
- [Psycopg parameter binding](https://www.psycopg.org/psycopg3/docs/basic/params.html)
