export const MEALS = ['breakfast', 'lunch', 'dinner', 'snack']

export function normalizeMeal(value) {
  return MEALS.includes(value) ? value : 'dinner'
}
