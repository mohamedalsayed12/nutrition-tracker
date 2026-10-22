import type { ActivityLevel, NutritionGoal, Sex } from "../types/api.ts"

export const activityChoices: Array<{ value: ActivityLevel; label: string; detail: string }> = [
  { value: "sedentary", label: "Sedentary", detail: "Mostly sitting, with little exercise beyond daily tasks." },
  { value: "lightly active", label: "Lightly active", detail: "Light movement on most days, such as walking." },
  { value: "moderately active", label: "Moderately active", detail: "Exercise, or time on your feet, for a good part of the day." },
  { value: "very active", label: "Very active", detail: "Hard exercise or a physical job on most days." },
  { value: "extra active", label: "Extra active", detail: "Very hard training, or a physical job plus extra workouts." },
]

export const goalChoices: Array<{ value: NutritionGoal; label: string; detail: string }> = [
  { value: "lose_weight", label: "Lose", detail: "About 500 kcal below the energy you use, without dropping under a safe floor." },
  { value: "maintain", label: "Maintain", detail: "Calories match the energy you use in a usual day." },
  { value: "gain_weight", label: "Gain", detail: "About 300 kcal above the energy you use." },
]

export const sexChoices: Array<{ value: Sex; label: string }> = [
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
]
