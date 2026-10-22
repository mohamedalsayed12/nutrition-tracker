import { describe, expect, it } from "vitest"
import { caloriesEaten, weeklyCalorieBars } from "./weeklySummary.ts"

describe("weekly calorie bars", () => {
  it("prefers the plain Energy record and buckets logs by local day", () => {
    expect(caloriesEaten([
      { name: "Energy (Atwater General Factors)", unit: "kcal", eaten: 10 },
      { name: "Energy", unit: "kcal", eaten: 80 },
    ])).toBe(80)

    const bars = weeklyCalorieBars([
      { logged_at: "2026-10-19T12:00:00Z", nutrients: [{ name: "Energy", unit: "kcal", eaten: 400 }] },
      { logged_at: "2026-10-19T18:00:00Z", nutrients: [{ name: "Energy", unit: "kcal", eaten: 150.4 }] },
      { logged_at: "2026-10-21T12:00:00Z", nutrients: [{ name: "Calories", unit: "kcal", eaten: 90 }] },
    ], "2026-10-19", "UTC")

    expect(bars.map((bar) => bar.calories)).toEqual([550, 0, 90, 0, 0, 0, 0])
    expect(bars[0]?.label).toBe("Mon")
    expect(bars.reduce((sum, bar) => sum + bar.calories, 0)).toBe(640)
  })
})
