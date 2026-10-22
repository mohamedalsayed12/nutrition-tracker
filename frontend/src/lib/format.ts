export function formatKcal(value: number): string {
  return `${Math.round(value).toLocaleString()} kcal`
}

export function formatGrams(value: number): string {
  return `${value.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} g`
}
