# Cursor prompt — Nutrition Tracker frontend

Paste everything below the line into Cursor (Agent mode), from the root of a new `frontend/` folder next to the backend.

---

You are building the frontend for my **Nutrition Tracker**. The backend already exists: a Flask API (Python, PostgreSQL, SQLAlchemy, flask-jwt-extended, Pydantic validation) that uses the USDA FoodData Central API for food data. Build a production-quality frontend that uses it. Don't change the backend unless I ask you to.

## Stack
- React 18 + Vite + TypeScript (strict mode)
- Tailwind CSS
- React Router v6
- TanStack Query for all server state (caching, loading, error, optimistic updates)
- React Hook Form + Zod for forms (mirror the backend's validation rules listed below)
- Recharts for charts
- No UI kit. Build small reusable components in `src/components/ui/`: Button, Input, Select, Card, Modal/Sheet, Tabs, ProgressRing, ProgressBar, Badge, EmptyState, Skeleton, Toast.

## Design direction
- Light, clean theme by default (warm off-white background, white cards, soft borders), with a dark mode toggle.
- Fonts: "Space Grotesk" (500/700) for headings and big numbers, "Public Sans" for body (Google Fonts).
- One accent colour for "on track", plus amber for "under target" and red only for limits that were exceeded (sodium, sugar, saturated fat).
- Mobile-first. Bottom tab bar on mobile (Today / Add / Weekly / Settings), left sidebar on desktop (≥1024px).
- Numbers are the hero: big calorie ring, clear macro bars, units always shown (kcal, g, mg, µg).
- Every list has a loading skeleton, an empty state and an error state with a retry button.

## Project structure
```
src/
  api/          client.ts (fetch wrapper) + one file per resource (auth, users, foodLogs, activityLogs, foods, goals, settings, reports)
  api/mock/     mock handlers for endpoints that don't exist yet
  hooks/        TanStack Query hooks (useDailyReport, useWeeklyReport, useFoodSearch, ...)
  components/   ui/ + feature components
  pages/        Login, Register, Onboarding, Today, AddFood, Weekly, History, Settings
  types/        TypeScript types for every request and response
  lib/          auth (token storage), dates/timezones, number formatting
```

## API client rules
- Base URL from `VITE_API_URL` (default `http://localhost:5000`). Every route lives under `/api/v1`.
- The backend serves an OpenAPI spec at `GET /openapi.json`. **Fetch it first and use it to check and generate the TypeScript types.** Where the spec and this prompt disagree, the spec wins. Tell me about any differences you find.
- Send `Authorization: Bearer <token>` on every authenticated request.
- On 401: clear the token and redirect to `/login`.
- **Error format:** all errors come back as `{ "error": "message" }`. A 400 validation error also has `details: [{ loc, msg, type }]`. Show `error` in a toast, and map `details[].loc` onto the matching form fields.
- Send the user's IANA timezone (`Intl.DateTimeFormat().resolvedOptions().timeZone`) as the `timezone` query param on every report call, so "today" means the user's local day.
- **CORS:** the backend only allows origins listed in its `FRONTEND_ORIGIN` env var. Note in the README that it must include `http://localhost:5173`.
- Add a `VITE_USE_MOCKS` flag. When it's true, or when an endpoint is listed under "Not built yet", route the call to `src/api/mock/`. Mocks return realistic data in the exact shapes below, with ~200ms delay. Each mocked endpoint must be swappable for the real one by changing a single line.

## Existing endpoints (real — use these exactly)

### Auth and user
- `POST /api/v1/users` — register. Body `{ name, email, password }`. Name 1–100 chars. Password 8–128 chars and at most 72 UTF-8 bytes. Returns `{ id, name, email }` (201). Returns 409 if the email is taken.
- `POST /api/v1/auth/login` — **JSON** body `{ email, password }` → `{ access_token, token_type: "Bearer" }`. Returns 401 on bad credentials.
- `GET /api/v1/users/me` → `{ id, name, email }`

### Goals and settings
- `GET /api/v1/goals/nutrition` → `{ configured: false }`, or `{ configured: true, age, sex, height_cm, weight_kg, activity_level, protein_min, protein_max, carbs, micronutrients }`
- `PUT /api/v1/goals/nutrition` — body `{ age (int 18–100), sex: "male"|"female", height_cm (50–300), weight_kg (20–500), activity_level: "sedentary"|"lightly active"|"moderately active"|"very active"|"extra active", goal: "maintain"|"lose_weight"|"gain_weight" }` → `{ bmr, tdee, calories, protein_min, protein_max, carbs, micronutrients }`
- `GET /api/v1/goals/calories` → `{ calories: number | null }`
- `PUT /api/v1/goals/calories` — body `{ calories (500–10000) }`
- `GET /api/v1/settings/macro-split` → `{ configured, carbs_percent, protein_percent, fat_percent }` (defaults 55/20/25)
- `PUT /api/v1/settings/macro-split` — the three percentages must add up to 100. Validate this live in the form.
- `DELETE /api/v1/settings/macro-split` — reset to defaults (204)
- `GET /api/v1/settings/health` and `PUT /api/v1/settings/health` — body `{ conditions: ("pregnancy"|"diabetes"|"ibs"|"menstruation")[], trimester: 1|2|3|null, custom_calories, custom_carbs, custom_protein, custom_fat (each nullable), micronutrient_overrides: { [name]: number } }`. Pregnancy and menstruation can't both be selected. Pregnancy requires a trimester. The response also includes `guidance`.

### Food search
- `GET /api/v1/foods?q=` — needs at least 2 characters. Returns `{ foods: [{ fdc_id, description, data_type, brand_name, gtin_upc }] }`. Returns 503 if search isn't configured, 502 if USDA is down. Show a friendly message for both.
- `GET /api/v1/foods/{fdc_id}/measures` → `{ measures: [{ code, label, grams }] }`, e.g. "1 cup (240 g)". Use these for the serving picker.
- `GET /api/v1/foods/frequent` → `{ breakfast: Item[], lunch: Item[], dinner: Item[], snack: Item[] }`, where `Item = { fdc_id, description, grams, count, last_logged }`

### Logs
- `GET /api/v1/food-logs?page=&per_page=` → `{ items: FoodLog[], total, page, per_page }`
- `POST /api/v1/food-logs` — body `{ meal: "breakfast"|"lunch"|"dinner"|"snack", fdc_id, grams (>0, ≤10000) }` → `FoodLog`
- `GET`, `PUT` (same body) and `DELETE` on `/api/v1/food-logs/{id}`
- `FoodLog = { id, meal, fdc_id, food_name, grams, nutrients, logged_at }`
- `GET /api/v1/activity-logs` (paginated the same way), `POST`, `GET/PUT/DELETE /{id}` — body `{ activity, activity_type: "walking"|"running"|"cycling"|"swimming"|"strength"|"yoga"|"other_light"|"other_moderate"|"other_vigorous", duration_minutes, weight_kg, height_cm, extra: boolean }`. Response includes `calories_burned`. Pre-fill weight and height from the nutrition goals.
- `GET /api/v1/exercises?q=` → `{ exercises: [...] }` for activity name autocomplete

### Reports
- `GET /api/v1/reports/daily?date=YYYY-MM-DD&timezone=` → `{ date, food_log_count, totals: { Calories, Protein, Carbohydrates, Fat }, reported, calorie_goal, exercise_credit, progress, fat_range, custom_macros, protein_min, protein_max, carbs, micronutrients: [{ name, unit, target, limit, logged, remaining, percent, partial }], condition_nutrition }`
- `GET /api/v1/reports/weekly?week_start=&timezone=` → `{ week_start, logged_days, food_count, macros: [{ name, unit, average, reported, total_foods, partial }], micros: [{ name, unit, average, target, limit, reported, total_foods, partial, status }] }`
- `PUT /api/v1/days/{YYYY-MM-DD}/save` — mark a day as complete. Returns 409 if no food is logged that day.
- `GET /api/v1/days` → `{ days: ["YYYY-MM-DD", ...] }`

**Partial data:** when `partial` is true, some foods didn't report that nutrient. Show a small "based on X of Y foods" note so totals aren't misleading.

## Not built yet (mock this, with this exact contract. I will build it in Flask)
The nutrient-density scoring logic already exists in `services/nutrient_scoring.py`, but no endpoint exposes it yet.
- `GET /api/v1/foods/{fdc_id}/score?grams=` → `{ fdc_id, calories_per_100g, score: number | null (0–100), reasons: string[], nutrients_per_100kcal: [{ name, unit, amount, percent_of_target }] }`

## Pages and features

### 1. Auth (`/login`, `/register`)
- Zod validation matching the backend rules above. Show backend errors inline. Log the user in automatically after registering.
- After login, if `GET /goals/nutrition` returns `configured: false`, send the user to `/onboarding`.

### 2. Onboarding (`/onboarding`)
- A 3-step wizard: (1) age, sex, height, weight; (2) activity level, explained in plain English; (3) goal.
- Submit to `PUT /goals/nutrition`, then show a results screen: BMR, TDEE, daily calories, protein range, carbs, with a one-line explanation of each. Then go to Today.

### 3. Today (`/`)
- Date switcher (previous/next day and a calendar). Days already saved show a check.
- A big calorie ring: eaten vs `calorie_goal`, with exercise credit shown separately ("+150 kcal from exercise").
- Macro bars: protein against its min–max band, carbs against target, fat against `fat_range`.
- A micronutrient list sorted by `percent`. Nutrients with `limit: true` are maximums, so going over turns them red. Collapse to the top 8 with a "Show all" option.
- Meals section (breakfast / lunch / dinner / snack): each food shows its name, grams and kcal, with swipe or menu actions to edit grams, move meal, or delete. "+ Add" on each meal opens Add Food with that meal pre-selected.
- Activities section with calories burned and a "+ Add activity" sheet.
- A "Save day" button using `PUT /days/{date}/save`.

### 4. Add Food (`/add?meal=lunch`)
- Meal selector chips.
- "Frequent" tab, filled from `/foods/frequent` for the chosen meal. One tap re-logs a food with its usual grams.
- Search tab with a 300ms debounce and a minimum of 2 characters. Results show description, brand and data type.
- Selecting a food opens a detail sheet:
  - Serving picker from `/measures`, plus custom grams. Quantity × measure grams gives total grams.
  - A live preview of the kcal and macros it adds.
  - A **nutrient density card** (from the mocked `/score` endpoint): a 0–100 score badge, top reasons, and a "per 100 kcal" table showing the % of the user's target each nutrient covers.
  - "Add to {meal}" posts to `/food-logs`, updates Today optimistically, and shows a toast with an Undo button that deletes the new log.

### 5. Weekly report (`/weekly`)
- Week switcher (Monday start), plus "X of 7 days logged".
- Average daily macros vs targets as a bar chart.
- Micronutrients grouped by `status` (met / low / over limit) with averages vs targets and "partial" notes.
- A short auto-generated summary at the top, e.g. "Protein on target 5/7 days · Low in fibre and vitamin D". Build it from the data in the frontend; don't add an endpoint for it.

### 6. History (`/history`)
- A calendar of saved days from `/days`. Tap a day to open Today for that date.
- A paginated list of past food logs from `/food-logs`.

### 7. Settings (`/settings`)
- Profile from `/users/me`, with logout.
- Edit nutrition goals (same form as onboarding).
- Calorie override (`/goals/calories`).
- Macro split: three linked sliders that always total 100, plus a "Reset to default" button.
- Health settings: condition toggles, a trimester picker that only shows when pregnancy is selected, custom macro overrides, and a display of the `guidance` text.
- Theme toggle.

## Quality bar
- Strict TypeScript, no `any`. Types in `src/types/` should come from `/openapi.json` where possible.
- Accessible: real `<button>`/`<label>` elements, visible focus states, keyboard-navigable modals and sheets, and progress rings with text equivalents for screen readers.
- Never use `dangerouslySetInnerHTML`.
- Format numbers with sensible precision: kcal as integers, grams to 1 decimal place, micros with their units.
- Add a README section covering how to run it (`npm i`, `npm run dev`), env vars, the CORS note, and a table showing which endpoints are real and which are mocked.
- Write Vitest tests for: the API client (401 redirect, error and `details` mapping), the macro-split "always totals 100" slider logic, serving × quantity → grams, timezone and date helpers, and the weekly summary generator.

## Build order
1. Scaffold the project, theme, UI components, API client and OpenAPI type check. Build the auth pages and confirm login works against the real backend.
2. Onboarding and Settings, since goals have to exist before reports mean anything.
3. Add Food (search, measures, frequent foods, logging).
4. Today dashboard.
5. Weekly report and History.
6. Mock the score endpoint and add the nutrient density card.
7. Polish, tests and README.

Stop after each step and tell me what you built and how to check it before moving on.
