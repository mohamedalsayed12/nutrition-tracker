import type { FoodScore } from "../../types/api.ts"

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms))

export async function mockFoodScore(fdcId: number, grams: number): Promise<FoodScore> {
  await wait(200)
  const scale = Math.min(Math.max(grams, 1), 10000) / 100
  return {
    fdc_id: fdcId,
    calories_per_100g: 165,
    score: 72,
    reasons: [
      "Protein provides a large share of your daily target per 100 kcal.",
      "Iron and vitamin B6 are reported for this food.",
      "Some micronutrients are missing from the USDA record, so they earn no points.",
    ],
    nutrients_per_100kcal: [
      { name: "Protein", unit: "g", amount: Number((18.8 / scale).toFixed(1)), percent_of_target: 14.2 },
      { name: "Iron", unit: "mg", amount: 0.4, percent_of_target: 6.1 },
      { name: "Vitamin B6", unit: "mg", amount: 0.3, percent_of_target: 18.4 },
      { name: "Sodium", unit: "mg", amount: 42, percent_of_target: 1.8 },
    ],
  }
}
