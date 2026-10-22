import { describe, expect, it } from "vitest"
import { adjustMacroSplit, macroGramTargets, normalizeMacroSplit, type MacroPercents } from "./macroSplit.ts"

function total(split: MacroPercents): number {
  return split.carbs_percent + split.protein_percent + split.fat_percent
}

describe("macro split", () => {
  it("keeps every adjustment at 100", () => {
    let split = { carbs_percent: 55, protein_percent: 20, fat_percent: 25 }
    const keys = ["carbs_percent", "protein_percent", "fat_percent"] as const
    for (const key of keys) {
      for (let value = 0; value <= 100; value += 7) {
        split = adjustMacroSplit(split, key, value)
        expect(total(split)).toBe(100)
        expect(split[key]).toBe(value)
      }
    }
  })

  it("rounds a messy split so the last field absorbs the remainder", () => {
    const split = normalizeMacroSplit({ carbs_percent: 55.4, protein_percent: 20.4, fat_percent: 25.2 })
    expect(split).toEqual({ carbs_percent: 55, protein_percent: 20, fat_percent: 25 })
    expect(total(split)).toBe(100)
  })

  it("turns a saved split into one gram target each", () => {
    expect(macroGramTargets(2933.1, { carbs_percent: 55, protein_percent: 20, fat_percent: 25 }, {
      carbs: null,
      protein: null,
      fat: null,
    })).toEqual({ carbs: 403.3, protein: 146.7, fat: 81.5 })
  })

  it("keeps a care-plan gram and gives the leftover calories to the other macros", () => {
    expect(macroGramTargets(2000, { carbs_percent: 55, protein_percent: 20, fat_percent: 25 }, {
      carbs: null,
      protein: 100,
      fat: null,
    })).toEqual({ carbs: 275, protein: 100, fat: 55.6 })
  })
})
