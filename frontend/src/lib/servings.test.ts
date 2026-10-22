import { describe, expect, it } from "vitest"
import { gramsFromServing } from "./servings.ts"

describe("gramsFromServing", () => {
  it("multiplies a serving by the quantity", () => {
    expect(gramsFromServing(100, 1.5)).toBe(150)
    expect(gramsFromServing(28.35, 2)).toBe(56.7)
  })

  it("rejects an empty serving, a zero quantity, and more than 10,000 g", () => {
    expect(() => gramsFromServing(0, 1)).toThrow(/serving/i)
    expect(() => gramsFromServing(100, 0)).toThrow(/quantity/i)
    expect(() => gramsFromServing(5000, 3)).toThrow(/10,000/)
  })
})
