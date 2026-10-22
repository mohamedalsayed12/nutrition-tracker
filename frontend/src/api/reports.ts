import { browserTimeZone } from "../lib/dates.ts"
import type { DailyReport, SaveDayResponse, SavedDaysResponse, WeeklyReport } from "../types/api.ts"
import { request } from "./client.ts"

export { browserTimeZone }

export function getDailyReport(date?: string, timezone = browserTimeZone()): Promise<DailyReport> {
  return request<DailyReport>("/reports/daily", { query: { date, timezone } })
}

export function getWeeklyReport(weekStart?: string, timezone = browserTimeZone()): Promise<WeeklyReport> {
  return request<WeeklyReport>("/reports/weekly", { query: { week_start: weekStart, timezone } })
}

export function saveDay(date: string): Promise<SaveDayResponse> {
  return request<SaveDayResponse>(`/days/${date}/save`, { method: "PUT" })
}

export function getSavedDays(): Promise<SavedDaysResponse> {
  return request<SavedDaysResponse>("/days")
}
