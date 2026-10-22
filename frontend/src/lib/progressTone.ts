export type IntakeTone = "accent" | "amber" | "danger"

export function intakeTone(percent: number | null, limit = false): IntakeTone {
  if (percent == null) return "amber"
  if (limit) return percent > 100 ? "danger" : "accent"
  if (percent > 100) return "danger"
  if (percent >= 90) return "accent"
  return "amber"
}
