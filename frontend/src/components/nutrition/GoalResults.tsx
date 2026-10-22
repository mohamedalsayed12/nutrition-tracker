import { formatGrams, formatKcal } from "../../lib/format.ts"
import type { NutritionSetupResponse } from "../../types/api.ts"

const rows = (result: NutritionSetupResponse) => [
  ["BMR", formatKcal(result.bmr), "Energy your body uses at rest, before activity."],
  ["TDEE", formatKcal(result.tdee), "BMR plus the activity level you selected."],
  ["Daily calories", formatKcal(result.calories), "Maintain matches TDEE. Lose is about 500 kcal under, with a floor. Gain is about 300 kcal over."],
  ["Protein", `${formatGrams(result.protein_min)} – ${formatGrams(result.protein_max)}`, "Minimum from your body weight, age and goal; maximum is 35% of calories."],
  ["Carbohydrates", formatGrams(result.carbs), "About 55% of the saved calorie target, until a care plan sets its own amount."],
]

export function GoalResults({ result }: { result: NutritionSetupResponse }) {
  return (
    <dl className="space-y-4">
      {rows(result).map(([label, value, detail]) => (
        <div key={label}>
          <dt className="text-sm text-muted">{label}</dt>
          <dd className="font-display text-2xl font-medium">{value}</dd>
          <dd className="mt-1 text-sm text-muted">{detail}</dd>
        </div>
      ))}
    </dl>
  )
}
