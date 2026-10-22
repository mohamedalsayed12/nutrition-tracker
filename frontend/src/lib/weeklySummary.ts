import { addDays, formatShortDay, isSameLocalDay } from "./dates.ts"

export type CalorieLog = {
  logged_at: string
  nutrients: Array<{ name: string; unit: string; eaten: number }>
}

export type DayCalories = {
  date: string
  label: string
  calories: number
}

export function caloriesEaten(nutrients: CalorieLog["nutrients"]): number {
  const ranked = nutrients
    .filter((item) => item.unit.toLowerCase() === "kcal" && item.name.toLowerCase().startsWith("energy"))
    .sort((left, right) => Number(left.name.toLowerCase() !== "energy") - Number(right.name.toLowerCase() !== "energy"))
  const match = ranked[0] ?? nutrients.find((item) => item.name === "Calories" && item.unit.toLowerCase() === "kcal")
  return match?.eaten ?? 0
}

export function weeklyCalorieBars(logs: CalorieLog[], weekStart: string, timeZone: string): DayCalories[] {
  return Array.from({ length: 7 }, (_, index) => {
    const date = addDays(weekStart, index)
    const calories = logs.reduce((total, log) => (
      isSameLocalDay(log.logged_at, date, timeZone) ? total + caloriesEaten(log.nutrients) : total
    ), 0)
    return { date, label: formatShortDay(date), calories: Math.round(calories) }
  })
}
