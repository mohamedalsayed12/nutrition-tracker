# Nutrition tracker frontend

React app for the Flask nutrition API in the parent folder. Sign-in, goals, settings, food logging, today, and the weekly report talk to the live API. The food score card is a preview.

## Run it

```powershell
npm install
npm run dev
```

The dev server starts at http://localhost:5173 and moves to the next free port if that one is taken.

Copy `.env.example` to `.env.local` if you don't already have one.

| Variable | Purpose |
| --- | --- |
| `VITE_API_URL` | API origin. The default in code is `http://localhost:5000`. This machine's API is running at `http://127.0.0.1:8765`. |
| `VITE_USE_MOCKS` | Reserved for swapping real calls to `src/api/mock/`. Food score is mocked either way, because that route does not exist yet. |

```powershell
npm test
npm run check:openapi
```

`npm test` covers the API error mapping, macro totals, serving math, dates, and the weekly calorie bars.

## CORS

The API only sends browser responses to origins in `FRONTEND_ORIGIN`. Include the Vite origin, and restart Flask after changing it:

```text
FRONTEND_ORIGIN=http://localhost:5173,http://localhost:5174
```

With this variable empty, the browser blocks every API call.

## What is real, and what is mocked

| Call | Status |
| --- | --- |
| Auth, profile, goals, settings | Real `/api/v1` routes |
| Food search, measures, frequent foods | Real |
| Food logs and activity logs | Real |
| Daily report, weekly report, saved days | Real. Reports send the browser's IANA timezone. |
| `GET /api/v1/foods/{fdc_id}/score` | Mocked in `src/api/mock/score.ts` until the backend adds it |

## Where the OpenAPI spec and the prompt differ

`GET /openapi.json` lists paths and request bodies. It does not describe response bodies, so `src/types/api.ts` follows the Flask routes.

- The spec's password is 8–128 characters. The server also rejects passwords over 72 UTF-8 bytes. Registration checks both.
- `GET /api/v1/foods/frequent` returns `{ foods: { breakfast, lunch, dinner, snack } }`.
- `PUT /api/v1/settings/macro-split` returns the three percentages. `configured` is only on GET.
- A missing or invalid JWT comes back as `{ "msg": "..." }`. App errors use `{ "error": "..." }`, and validation errors add `details`.
- The API stores calculated targets, not the goal name. Settings opens that choice at Maintain.
- Once health settings exist, saving the daily calorie target also writes the care-plan calorie number.
- Saved days are matched in UTC on the server. The daily and weekly reports use the timezone query.
- There is no score path in the spec.
