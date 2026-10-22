export function browserTimeZone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
}

export function localDateISO(date = new Date(), timeZone = browserTimeZone()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date)
}

export function addDays(isoDate: string, days: number): string {
  const [year, month, day] = isoDate.split("-").map(Number)
  const date = new Date(Date.UTC(year ?? 1970, (month ?? 1) - 1, day ?? 1))
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}

export function startOfWeek(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number)
  const date = new Date(Date.UTC(year ?? 1970, (month ?? 1) - 1, day ?? 1))
  const weekday = date.getUTCDay()
  const mondayOffset = weekday === 0 ? 6 : weekday - 1
  return addDays(isoDate, -mondayOffset)
}

export function formatDayLabel(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number)
  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(year ?? 1970, (month ?? 1) - 1, day ?? 1)))
}

export function formatShortDay(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number)
  return new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(year ?? 1970, (month ?? 1) - 1, day ?? 1)))
}

export function isSameLocalDay(isoTimestamp: string, day: string, timeZone: string): boolean {
  const parsed = new Date(isoTimestamp)
  if (Number.isNaN(parsed.getTime())) return false
  return localDateISO(parsed, timeZone) === day
}
