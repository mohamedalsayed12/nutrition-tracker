# Voice logging on iOS, Android, and Siri

Yes — people can log food by voice on phones, and they can do it **from outside the app** (Siri / Google Assistant) once you wire a shortcut to this API or open the app with a deep link.

## What works today

| Surface | How |
| --- | --- |
| In-app (web) | **Speak what you ate** on Add food (Web Speech API; Chrome works best) |
| Deep link into the app | Open Add food with a transcript or start the mic |
| Outside the app (Siri / Assistant) | Shortcut / routine that POSTs to `/api/v1/food-logs/from-voice` or opens a deep link |

Native App Store apps with first-class **App Intents** (iOS) or **App Actions** (Android) are the polished long-term path. You can still use Siri *now* via Shortcuts against this backend.

## Deep links (open the web app)

Examples (replace the origin with your deployed frontend):

```text
https://YOUR_FRONTEND/app/add?transcript=180%20grams%20of%20chicken%20for%20dinner
https://YOUR_FRONTEND/app/add?transcript=two%20eggs%20for%20breakfast&auto_log=1
https://YOUR_FRONTEND/app/add?speak=1
https://YOUR_FRONTEND/app/add?barcode=012345678905
```

- `transcript` / `say` / `q` — parse the sentence, fill grams + meal, suggest a USDA match  
- `auto_log=1` — parse **and** create the food log immediately, then return to Today  
- `speak=1` — open Add food and start the microphone  
- `barcode=` — look up a packaged product  

## One-shot API for assistants

```http
POST /api/v1/food-logs/from-voice
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "transcript": "180 grams of chicken breast for dinner",
  "default_meal": "snack",
  "auto_log": true
}
```

Response includes the parsed meal/grams, suggested foods, and the created `logged` food entry when `auto_log` is true.

Get a token the same way as the app: `POST /api/v1/auth/login` with email/password.

## iOS — Siri Shortcuts (outside the app)

1. Open the **Shortcuts** app → **+** → name it e.g. **Log food**.
2. Add **Ask for Input** (or **Dictate Text**) → Prompt: `What did you eat?`
3. Add **Get Contents of URL**:
   - URL: `https://YOUR_API/api/v1/food-logs/from-voice`
   - Method: `POST`
   - Headers: `Authorization` = `Bearer YOUR_TOKEN`, `Content-Type` = `application/json`
   - Request body (JSON):

```json
{
  "transcript": "Ask for Input result",
  "auto_log": true
}
```

4. Optional: add **Show Notification** with the response summary.
5. Tap the shortcut settings → **Add to Siri** → record a phrase like **“Log my food”**.

Then: **“Hey Siri, log my food”** → speak *“two eggs for breakfast”* → the API logs it.

### Safer token handling

Do not paste a long-lived password into a shortcut if you can avoid it. Prefer:

- a short-lived access token you refresh occasionally, or  
- opening the deep link instead of calling the API directly:

**Open URLs** →  
`https://YOUR_FRONTEND/app/add?transcript=DICTIONATED_TEXT&auto_log=1`  
(user must already be signed in on that device browser / PWA).

### Fully native Siri (later)

A Capacitor / React Native / Swift wrapper can expose **App Intents** so Siri understands phrases like “Log chicken in Nutrition Tracker” without a custom Shortcut. That needs a native iOS target and App Store distribution.

## Android — Google Assistant

1. Open **Google Assistant routines** (or the **Shortcuts** app if installed).
2. Trigger phrase: e.g. **“log my food”**.
3. Action options:
   - **Open URL / browse**:  
     `https://YOUR_FRONTEND/app/add?speak=1` or with `transcript=...&auto_log=1`
   - Or **HTTP Request** (via Tasker / HTTP Shortcut apps) to  
     `POST /api/v1/food-logs/from-voice` with the bearer token

Assistant App Actions inside a Play Store app are the native equivalent of iOS App Intents.

## Mic quality on phones

| Platform | In-browser mic | Outside app |
| --- | --- | --- |
| Android Chrome | Good | Assistant routine / deep link |
| iOS Safari | Limited Web Speech support | Prefer **Siri Shortcut → API or deep link** |
| Installed PWA | Same as browser | Same deep links |
| Native shell (Capacitor, etc.) | Native speech APIs | App Intents / App Actions |

## Security notes

- Treat bearer tokens in Shortcuts like passwords.
- `auto_log=true` will write a food log as soon as the best USDA match is found — good for Siri, so keep phrases specific (“chicken breast 180 grams”, not just “food”).
- Rotate tokens if a phone is shared or lost.
