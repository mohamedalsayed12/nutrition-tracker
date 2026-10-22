export type MacroPercents = {
  carbs_percent: number
  protein_percent: number
  fat_percent: number
}

const keys = ["carbs_percent", "protein_percent", "fat_percent"] as const

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

export function normalizeMacroSplit(split: MacroPercents): MacroPercents {
  const carbs = clamp(Math.round(split.carbs_percent), 0, 100)
  const protein = clamp(Math.round(split.protein_percent), 0, 100 - carbs)
  return { carbs_percent: carbs, protein_percent: protein, fat_percent: 100 - carbs - protein }
}

const gramFactors = { carbs: 4, protein: 4, fat: 9 } as const

export type MacroGrams = Record<keyof typeof gramFactors, number>

export function macroGramTargets(
  calories: number,
  split: MacroPercents,
  custom: { carbs: number | null; protein: number | null; fat: number | null },
): MacroGrams {
  const keys = ["carbs", "protein", "fat"] as const
  const percentages = {
    carbs: split.carbs_percent,
    protein: split.protein_percent,
    fat: split.fat_percent,
  }
  const remaining = calories - keys.reduce((sum, name) => {
    const amount = custom[name]
    return amount == null ? sum : sum + amount * gramFactors[name]
  }, 0)
  const openShare = keys.reduce((sum, name) => (custom[name] == null ? sum + percentages[name] : sum), 0)
  return Object.fromEntries(keys.map((name) => {
    const amount = custom[name]
    if (amount != null) return [name, amount]
    if (openShare <= 0) return [name, 0]
    const grams = Math.max(remaining, 0) * percentages[name] / openShare / gramFactors[name]
    return [name, Math.round(grams * 10) / 10]
  })) as MacroGrams
}

export function adjustMacroSplit(current: MacroPercents, key: keyof MacroPercents, raw: number): MacroPercents {
  const next = clamp(Math.round(raw), 0, 100)
  const others = keys.filter((item) => item !== key)
  const firstKey = others[0]
  const secondKey = others[1]
  if (!firstKey || !secondKey) return current
  const remainder = 100 - next
  const otherTotal = current[firstKey] + current[secondKey]
  const firstShare = otherTotal <= 0 ? remainder / 2 : (remainder * current[firstKey]) / otherTotal
  const first = clamp(Math.round(firstShare), 0, remainder)
  return normalizeMacroSplit({
    ...current,
    [key]: next,
    [firstKey]: first,
    [secondKey]: remainder - first,
  })
}
