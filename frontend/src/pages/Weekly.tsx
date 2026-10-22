import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { Navigate } from "react-router-dom"
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { listRecentFoodLogs } from "../api/foodLogs.ts"
import { getDailyReport, getSavedDays, getWeeklyReport } from "../api/reports.ts"
import { Badge } from "../components/ui/Badge.tsx"
import { Button } from "../components/ui/Button.tsx"
import { Card } from "../components/ui/Card.tsx"
import { EmptyState } from "../components/ui/EmptyState.tsx"
import { Skeleton } from "../components/ui/Skeleton.tsx"
import { useNutrition } from "../hooks/useNutrition.ts"
import { addDays, browserTimeZone, formatDayLabel, localDateISO, startOfWeek } from "../lib/dates.ts"
import { formatKcal } from "../lib/format.ts"
import { weeklyCalorieBars } from "../lib/weeklySummary.ts"
import type { MicroAverage } from "../types/api.ts"

export function WeeklyPage() {
  const nutrition = useNutrition()
  const zone = browserTimeZone()
  const [weekStart, setWeekStart] = useState(() => startOfWeek(localDateISO(new Date(), zone)))
  const [historyDate, setHistoryDate] = useState<string | null>(null)
  const report = useQuery({
    queryKey: ["reports", "weekly", weekStart, zone],
    queryFn: () => getWeeklyReport(weekStart, zone),
  })
  const logs = useQuery({ queryKey: ["food-logs", "recent"], queryFn: listRecentFoodLogs })
  const saved = useQuery({ queryKey: ["days"], queryFn: getSavedDays })
  const history = useQuery({
    queryKey: ["reports", "daily", historyDate, zone],
    queryFn: () => getDailyReport(historyDate ?? undefined, zone),
    enabled: historyDate != null,
  })

  if (nutrition.isLoading || report.isLoading) return <Skeleton className="h-64 w-full" />
  if (nutrition.data && !nutrition.data.configured) return <Navigate to="/onboarding" replace />
  if (report.isError || !report.data) {
    return (
      <EmptyState
        title="Couldn't load the week"
        body="The weekly report didn't come back. Check that the API is running, then try again."
        action={<Button onClick={() => void report.refetch()}>Retry</Button>}
      />
    )
  }

  const bars = weeklyCalorieBars(logs.data ?? [], weekStart, zone)
  const weekEnd = addDays(weekStart, 6)

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-medium">Weekly</h1>
          <p className="text-sm text-muted">{formatDayLabel(weekStart)} – {formatDayLabel(weekEnd)}</p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" onClick={() => setWeekStart(addDays(weekStart, -7))}>Previous</Button>
          <Button size="sm" variant="secondary" onClick={() => setWeekStart(addDays(weekStart, 7))}>Next</Button>
        </div>
      </div>
      <Card>
        <h2 className="font-display text-xl font-medium">Calories by day</h2>
        <p className="mt-1 text-sm text-muted">{report.data.logged_days} days with food · {report.data.food_count} foods</p>
        <div className="mt-4 h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bars}>
              <XAxis dataKey="label" tick={{ fill: "#5d675e", fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#5d675e", fontSize: 12 }} axisLine={false} tickLine={false} width={36} />
              <Tooltip formatter={(value) => [typeof value === "number" ? formatKcal(value) : value, "Calories"]} />
              <Bar dataKey="calories" fill="#1b7a43" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
      <Card className="space-y-3">
        <h2 className="font-display text-xl font-medium">Daily averages</h2>
        {report.data.macros.map((macro) => (
          <p key={macro.name} className="flex justify-between gap-3 text-sm">
            <span className="font-semibold">{macro.name}</span>
            <span className="text-muted">
              {macro.average == null ? "Not reported" : `${macro.average} ${macro.unit}`}
              {macro.partial ? " · partial" : ""}
            </span>
          </p>
        ))}
      </Card>
      <Card>
        <details>
          <summary className="cursor-pointer font-display text-xl font-medium">Micronutrient averages</summary>
          <ul className="mt-4 space-y-3">
            {report.data.micros.map((item) => (
              <li key={item.name} className="flex items-start justify-between gap-3 text-sm">
                <span>
                  <span className="block font-semibold">{item.name}</span>
                  <span className="text-muted">{item.average == null ? "Not reported" : `${item.average} ${item.unit} average · target ${item.target}`}</span>
                </span>
                <MicroBadge item={item} />
              </li>
            ))}
          </ul>
        </details>
      </Card>
      <Card>
        <h2 className="font-display text-xl font-medium">Saved days</h2>
        {saved.isLoading ? <Skeleton className="mt-4 h-12 w-full" /> : null}
        {saved.data && saved.data.days.length === 0 ? <p className="mt-3 text-sm text-muted">Save a day from Today and it will be listed here.</p> : null}
        <ul className="mt-3 flex flex-wrap gap-2">
          {saved.data?.days.map((day) => (
            <li key={day}>
              <Button size="sm" variant={historyDate === day ? "primary" : "secondary"} onClick={() => setHistoryDate(day)}>{day}</Button>
            </li>
          ))}
        </ul>
        {historyDate && history.isLoading ? <Skeleton className="mt-4 h-16 w-full" /> : null}
        {history.data ? (
          <div className="mt-4">
            <p className="font-semibold">{formatDayLabel(history.data.date)}</p>
            <p className="mt-1 text-sm text-muted">
              {formatKcal(history.data.totals.Calories)}
              {history.data.calorie_goal == null ? "" : ` of ${formatKcal(history.data.calorie_goal)}`}
              {` · ${history.data.food_log_count} foods`}
            </p>
          </div>
        ) : null}
      </Card>
    </div>
  )
}

function MicroBadge({ item }: { item: MicroAverage }) {
  const tone = item.status.startsWith("Above") ? "danger" : item.status.startsWith("Target") || item.status.startsWith("Within") ? "accent" : item.status.startsWith("Below") || item.status.startsWith("Partial") ? "amber" : "neutral"
  return <Badge tone={tone}>{item.status}</Badge>
}
