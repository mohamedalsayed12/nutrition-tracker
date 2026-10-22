import { readFileSync } from "node:fs"

const spec = JSON.parse(readFileSync(new URL("../openapi.json", import.meta.url), "utf8"))
const paths = spec.paths ?? {}
const required = [
  "/api/v1/users",
  "/api/v1/users/me",
  "/api/v1/auth/login",
  "/api/v1/goals/nutrition",
  "/api/v1/goals/calories",
  "/api/v1/settings/macro-split",
  "/api/v1/settings/health",
  "/api/v1/foods",
  "/api/v1/foods/frequent",
  "/api/v1/foods/{fdc_id}/measures",
  "/api/v1/food-logs",
  "/api/v1/food-logs/{log_id}",
  "/api/v1/activity-logs",
  "/api/v1/activity-logs/{log_id}",
  "/api/v1/exercises",
  "/api/v1/reports/daily",
  "/api/v1/reports/weekly",
  "/api/v1/days",
  "/api/v1/days/{day}/save",
]

const missing = required.filter((path) => !paths[path])
if (missing.length) {
  console.error("OpenAPI spec is missing paths the client calls:")
  for (const path of missing) console.error(`  ${path}`)
  process.exit(1)
}

const scorePath = "/api/v1/foods/{fdc_id}/score"
const responsesWithSchema = []
for (const [path, operations] of Object.entries(paths)) {
  for (const [method, operation] of Object.entries(operations)) {
    const success = operation.responses?.["200"] ?? operation.responses?.["201"]
    if (success?.content) responsesWithSchema.push(`${method.toUpperCase()} ${path}`)
  }
}

const password = paths["/api/v1/users"]?.post?.requestBody?.content?.["application/json"]?.schema?.properties?.password
console.log(`OpenAPI ${spec.openapi} — ${required.length} client paths are present.`)
console.log(paths[scorePath] ? "Score path is now in the spec." : "Score path is absent, so the client keeps using the mock.")
console.log(responsesWithSchema.length
  ? `Response schemas found: ${responsesWithSchema.join(", ")}`
  : "No success response in the spec includes a schema. Response types follow the Flask route code.")
console.log(password?.maxLength === 128 && password.minLength === 8 && !password.format
  ? "UserCreate password in the spec is 8–128 characters and does not mention the 72-byte server rule."
  : "UserCreate password schema differs from the last check. Review src/lib/schemas.ts.")
