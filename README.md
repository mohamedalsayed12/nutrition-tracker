# Nutrition Tracker API

I'm building this nutrition tracker so people can log food and activity, set goals, and see how a day or week compares with those goals. I kept the backend separate so I can add a web or mobile app later without rebuilding the calculations.

The backend uses Flask, PostgreSQL, and SQLAlchemy. It has server-rendered pages for login, registration, the meals log, targets and health settings (session login), plus a React frontend in `frontend/`. API clients sign in with JWT access tokens.

## What I've built so far

- Accounts, login, and user-specific food and activity logs.
- Food lookup through USDA FoodData Central, with nutrients calculated on the server.
- Food search ranked like Cronometer: everyday generic foods first ("Milk, whole" before "Coconut milk"), processed variants lower, branded products after, and foods you have logged before at the top. Servings list household portions first and pre-select one, such as "1 medium".
- Calorie and nutrient targets, macro split settings, and health preferences.
- Daily reports, weekly recaps, saved days, and frequently logged foods.
- A per-meal iron check: vitamin C only helps iron absorption when it is eaten in the same meal, so the daily report flags meals with iron but little vitamin C and suggests what to add (shown more prominently when periods are selected).
- PostgreSQL migrations, Docker setup, OpenAPI documentation, and automated tests.

Food search needs a USDA API key, and exercise search needs an API Ninjas key. Open `/login` for the meals log. The API runs on Heroku and stores records in Heroku Postgres.

## How I organised it

I split the routes, validation, calculations, and database work into separate parts so the API is easier to extend. I used the same general separation of responsibilities as my [Gym Social Media API](https://github.com/mohamedalsayed12/gym-social-media), with Flask Blueprints for the routes.

| Module | Responsibility |
| --- | --- |
| `main.py` | Application factory and extension initialization. |
| `app.py` | WSGI entry point and a factory import for Flask tools. |
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
| `.github/workflows/build-deploy.yml` | PostgreSQL tests, Alembic upgrade, Heroku deploy, and optional Docker publishing. |

A request moves from a route to a Pydantic schema, then a service, a SQLAlchemy model, and PostgreSQL. I check that the user in a JWT still exists, and I scope resource queries to the signed-in user.

## Run it locally

From the project directory in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
docker compose up -d database
.\.venv\Scripts\python.exe -m flask --app main db upgrade
.\.venv\Scripts\python.exe -m flask --app main run --debug --port 8000
```

Start with `.env.example` and put your local settings in an ignored `.env`. The database container exposes PostgreSQL on `127.0.0.1:5432` and keeps its data in a named Docker volume. Set `DATABASE_HOSTNAME` to `localhost` when Flask runs on Windows, or `database` when it runs in Compose. SQLAlchemy builds the connection URL from separate fields, including passwords with special characters. You can also supply `DATABASE_URL`, which takes precedence. The app and tests both need PostgreSQL.

Use different random values for `SECRET_KEY` and `JWT_SECRET_KEY`. Add `FDC_API_KEY` for USDA food search and logging, and `API_NINJAS_KEY` for exercise search. Set `FRONTEND_ORIGIN` to the exact origin of a future frontend; you can separate multiple origins with commas. Access tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES`, which defaults to 30.

To run both the API and PostgreSQL in containers:

```powershell
docker compose up -d --build
```

The API container applies migrations before starting Gunicorn on port 8000. `/api/v1/health` checks the application; `/api/v1/ready` checks the PostgreSQL connection.

## Using the API

`GET /openapi.json` gives you the full request and response schema if you want to build a frontend. The application routes return JSON, including errors.

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
| `GET /api/v1/reports/daily` | Read daily totals, targets, and exercise credit. |
| `GET /api/v1/reports/weekly` | Read a seven day nutrition recap. |
| `PUT /api/v1/days/{YYYY-MM-DD}/save` | Save a logged UTC day. |
| `GET /api/v1/days` | Read saved UTC days. |

Protected routes require `Authorization: Bearer <access_token>`. Food and activity listings accept `page` and `per_page` (maximum 100). Daily reports accept `date=YYYY-MM-DD`; weekly reports accept `week_start=YYYY-MM-DD`. Reports accept an IANA `timezone`, such as `Europe/London`, and default to UTC. Saved days use UTC; changing or deleting food logs reopens their saved day.

Food log creation and replacement use:

```json
{"meal": "breakfast", "fdc_id": 123456, "grams": 50}
```

Nutrient amounts come from USDA on the server. Allowed meals are `breakfast`, `lunch`, `dinner`, and `snack`.

Nutrition setup uses:

```json
{"age": 30, "sex": "male", "height_cm": 175, "weight_kg": 75, "activity_level": "moderately active", "goal": "maintain"}
```

I kept the nutrition calculations and source-linked condition guidance in backend services. You need to finish nutrition setup before logging activity. Check `/openapi.json` for the exact field rules and allowed values.

## Changing the database

I use migrations for schema changes. Starting Flask does not create or alter tables.

```powershell
.\.venv\Scripts\python.exe -m flask --app main db migrate -m "Describe the schema change"
.\.venv\Scripts\python.exe -m flask --app main db upgrade
```

Review a generated migration before applying it. The initial revision supports the existing tracker schema, including two historical health preference columns. I transferred the existing tracker records to PostgreSQL. Food search and serving sizes use the USDA API, so they need `FDC_API_KEY`.

SQLAlchemy binds values separately from SQL, so I don't put user input directly into query strings.

## Tests and CI

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The tests use a separate PostgreSQL database named `nutrition_test` by default, with connection settings from `.env`. Create it once with `docker compose exec -T database createdb -U nutrition nutrition_test`. You can use `TEST_DATABASE_URL` for a different dedicated database, as long as its name ends in `_test`. The tests create and remove tables, so don't point them at your application database. CI starts PostgreSQL 16, applies migrations, and runs the suite against its own test database.

Docker publishing is optional: set the repository variable `PUBLISH_DOCKER_IMAGE=true` and production environment secrets `DOCKER_HUB_USERNAME` and `DOCKER_HUB_ACCESS_TOKEN`. Successful main branch builds then publish `<username>/nutrition-tracker:latest`.

## Heroku and CI/CD

The Heroku app [nutrition-tracker-alsayed](https://nutrition-tracker-alsayed-90b0d9adaf0f.herokuapp.com/) runs this API on Python 3.14. The Heroku Postgres addon sets `DATABASE_URL`. The app turns Heroku's `postgres://` URL into `postgresql+psycopg` and requires SSL for every host except localhost and the local Docker database.

Each Heroku release applies the Alembic migrations in `migrations/` before Gunicorn starts:

```text
release: python -m flask --app main db upgrade
web: gunicorn --bind 0.0.0.0:$PORT "main:create_app()"
```

GitHub Actions runs on every push and pull request. The `build` job starts PostgreSQL 16, runs `flask db upgrade`, then pytest. A push to `main` that passes those tests deploys by pushing to Heroku. That job uses the `production` environment secret `HEROKU_API_KEY`. Heroku config vars, separate from the local `.env`, are `SECRET_KEY`, `JWT_SECRET_KEY`, `FDC_API_KEY`, `API_NINJAS_KEY`, and `FRONTEND_ORIGIN`. The addon owns `DATABASE_URL`.

`/api/v1/health` checks the process. `/api/v1/ready` checks PostgreSQL.

Do not commit production credentials.

## Using it on a phone

The site is a Progressive Web App, so it can be installed from the browser:

- **iPhone (Safari):** open the site, tap Share, then **Add to Home Screen**.
- **Android (Chrome):** open the site, tap the menu, then **Install app** (or **Add to Home screen**).

It then opens full screen from its own icon. `routers/pwa.py` serves the manifest, icons and
`pwa/sw.js`. The service worker keeps only the icons and an offline page on the phone; pages and
the API always come from the network, so logged data is never out of date.

## Framework references

- [Flask application factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/)
- [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/)
- [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/)
- [SQLAlchemy bound parameters](https://docs.sqlalchemy.org/en/20/tutorial/dbapi_transactions.html)
- [Psycopg parameter binding](https://www.psycopg.org/psycopg3/docs/basic/params.html)
