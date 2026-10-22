import type { Meal } from "../types/api.ts"

export const mealOptions: Array<{ id: Meal; label: string }> = [
  { id: "breakfast", label: "Breakfast" },
  { id: "lunch", label: "Lunch" },
  { id: "dinner", label: "Dinner" },
  { id: "snack", label: "Snack" },
]
