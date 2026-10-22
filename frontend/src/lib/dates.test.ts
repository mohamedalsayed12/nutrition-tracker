import { describe, expect, it } from "vitest"
import { addDays, isSameLocalDay, localDateISO, startOfWeek } from "./dates.ts"

describe("dates", () => {
  it("formats a calendar day in the requested timezone", () => {
    expect(localDateISO(new Date("2026-10-21T23:30:00Z"), "Europe/London")).toBe("2026-10-22")
    expect(localDateISO(new Date("2026-10-21T22:30:00Z"), "Europe/London")).toBe("2026-10-21")
  })

  it("starts weeks on Monday and steps across month boundaries", () => {
    expect(startOfWeek("2026-10-21")).toBe("2026-10-19")
    expect(startOfWeek("2026-10-25")).toBe("2026-10-19")
    expect(addDays("2026-10-31", 1)).toBe("2026-11-01")
    expect(isSameLocalDay("2026-10-21T23:30:00Z", "2026-10-22", "Europe/London")).toBe(true)
  })
})
