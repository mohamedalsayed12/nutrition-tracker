import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { Link, Navigate } from "react-router-dom"
import { z } from "zod"
import { ApiError } from "../api/client.ts"
import { createActivityLog, deleteActivityLog, listRecentActivityLogs } from "../api/activityLogs.ts"
import { deleteFoodLog, listRecentFoodLogs } from "../api/foodLogs.ts"
import { getDailyReport, getSavedDays, saveDay } from "../api/reports.ts"
import { getHealthSettings, getMacroSplit } from "../api/settings.ts"
import { Button } from "../components/ui/Button.tsx"
import { Card } from "../components/ui/Card.tsx"
import { EmptyState } from "../components/ui/EmptyState.tsx"
import { Input } from "../components/ui/Input.tsx"
import { ProgressBar } from "../components/ui/ProgressBar.tsx"
import { ProgressRing } from "../components/ui/ProgressRing.tsx"
import { Select } from "../components/ui/Select.tsx"
import { Skeleton } from "../components/ui/Skeleton.tsx"
import { useToast } from "../components/ui/Toast.tsx"
import { useCurrentUser } from "../hooks/useCurrentUser.ts"
import { useNutrition } from "../hooks/useNutrition.ts"
import { browserTimeZone, formatDayLabel, isSameLocalDay, localDateISO } from "../lib/dates.ts"
import { formatGrams, formatKcal } from "../lib/format.ts"
import { macroGramTargets } from "../lib/macroSplit.ts"
import { mealOptions } from "../lib/meals.ts"
import { intakeTone } from "../lib/progressTone.ts"
import type { ActivityType, FoodLog, NutritionGoals } from "../types/api.ts"

const activityTypes: Array<{ value: ActivityType; label: string }> = [
  { value: "walking", label: "Walking" },
  { value: "running", label: "Running" },
  { value: "cycling", label: "Cycling" },
  { value: "swimming", label: "Swimming" },
  { value: "strength", label: "Strength" },
  { value: "yoga", label: "Yoga" },
  { value: "other_light", label: "Other light" },
  { value: "other_moderate", label: "Other moderate" },
  { value: "other_vigorous", label: "Other vigorous" },
]

const activitySchema = z.object({
  activity: z.string().trim().min(1, "Name the activity.").max(200, "Use 200 characters or fewer."),
  activity_type: z.enum(["walking", "running", "cycling", "swimming", "strength", "yoga", "other_light", "other_moderate", "other_vigorous"]),
  duration_minutes: z.string().trim().min(1, "Enter the minutes.").refine((value) => {
    const number = Number(value)
    return Number.isFinite(number) && number > 0 && number <= 1440
  }, "Minutes must be greater than 0 and at most 1,440."),
  extra: z.boolean(),
})

type ActivityInput = z.infer<typeof activitySchema>

export function TodayPage() {
  const user = useCurrentUser()
  const nutrition = useNutrition()
  const zone = browserTimeZone()
  const [today] = useState(() => localDateISO(new Date(), browserTimeZone()))
  const report = useQuery({ queryKey: ["reports", "daily", today, zone], queryFn: () => getDailyReport(today, zone) })
  const logs = useQuery({ queryKey: ["food-logs", "recent"], queryFn: listRecentFoodLogs })
  const activities = useQuery({ queryKey: ["activity-logs", "recent"], queryFn: listRecentActivityLogs })
  const saved = useQuery({ queryKey: ["days"], queryFn: getSavedDays })
  const macros = useQuery({ queryKey: ["settings", "macros"], queryFn: getMacroSplit })
  const health = useQuery({ queryKey: ["settings", "health"], queryFn: getHealthSettings })

  if (nutrition.isLoading || user.isLoading || report.isLoading || macros.isLoading || health.isLoading) {
    return (
      <div className="space-y-4" aria-busy="true">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-44 w-full" />
      </div>
    )
  }
  if (nutrition.data && !nutrition.data.configured) return <Navigate to="/onboarding" replace />
  if (report.isError || !report.data || nutrition.isError || !nutrition.data) {
    return (
      <EmptyState
        title="Couldn't load today"
        body="The daily report didn't come back. Check that the API is running, then try again."
        action={<Button onClick={() => void report.refetch()}>Retry</Button>}
      />
    )
  }

  const dayLogs = (logs.data ?? []).filter((log) => isSameLocalDay(log.logged_at, today, zone))
  const dayActivities = (activities.data ?? []).filter((log) => isSameLocalDay(log.logged_at, today, zone))
  const logged = report.data.totals.Calories
  const goal = report.data.calorie_goal
  const tone = goal == null || goal <= 0 ? "accent" : intakeTone((logged / goal) * 100)
  const grams = goal == null ? null : macroGramTargets(goal, macros.data ?? { carbs_percent: 55, protein_percent: 20, fat_percent: 25 }, {
    carbs: health.data?.custom_carbs ?? null,
    protein: health.data?.custom_protein ?? null,
    fat: health.data?.custom_fat ?? null,
  })

  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm font-semibold text-accent">{formatDayLabel(today)}</p>
        <h1 className="font-display text-3xl font-medium">{user.data ? `Hi ${user.data.name}` : "Today"}</h1>
      </div>
      <Card className="flex flex-col items-center gap-4 sm:flex-row sm:items-center">
        <ProgressRing value={logged} max={goal ?? 0} label="Calories today" unit="kcal" tone={tone} caption={goal == null ? "No calorie target is saved." : undefined} />
        <div className="text-center sm:text-left">
          <p className="font-semibold">{goal == null ? "No calorie target" : `${formatKcal(logged)} of ${formatKcal(goal)}`}</p>
          <p className="mt-1 text-sm text-muted">
            {report.data.exercise_credit > 0 ? `Includes ${formatKcal(report.data.exercise_credit)} from extra exercise. ` : ""}
            Green is on track, amber is under the target, and red is over a limit.
          </p>
        </div>
      </Card>
      <Card className="space-y-4">
        <h2 className="font-display text-xl font-medium">Targets</h2>
        {report.data.progress.length === 0 ? <p className="text-sm text-muted">Save a calorie target to see progress.</p> : report.data.progress.map((item) => {
          const target = targetFor(item.name, goal, grams)
          const logged = item.logged ?? 0
          const percent = target != null && target > 0 ? (logged / target) * 100 : null
          return (
            <ProgressBar
              key={item.name}
              label={item.name}
              value={percent ?? 0}
              tone={intakeTone(percent)}
              detail={`${logged} ${item.unit} · ${targetText(item.name, target, item.target_label)}${item.partial ? " · partial" : ""}`}
            />
          )
        })}
        {report.data.condition_nutrition.fiber_goal != null ? (
          <ProgressBar
            label="Fiber"
            value={report.data.condition_nutrition.fiber_percent ?? 0}
            tone={intakeTone(report.data.condition_nutrition.fiber_percent)}
            detail={`${report.data.condition_nutrition.fiber_logged ?? 0} g · ${report.data.condition_nutrition.fiber_goal} g`}
          />
        ) : null}
      </Card>
      <Card>
        <div className="flex items-center justify-between gap-3">
          <h2 className="font-display text-xl font-medium">Meals</h2>
          <Link className="text-sm font-semibold text-accent underline-offset-4 hover:underline" to="/add">Add food</Link>
        </div>
        {logs.isLoading ? <Skeleton className="mt-4 h-16 w-full" /> : null}
        {logs.isError ? <p className="mt-3 text-sm text-danger">Meals could not be loaded.</p> : null}
        {!logs.isLoading && dayLogs.length === 0 ? <p className="mt-3 text-sm text-muted">Nothing logged yet today.</p> : null}
        <div className="mt-4 space-y-4">
          {mealOptions.map((meal) => {
            const items = dayLogs.filter((log) => log.meal === meal.id)
            if (items.length === 0) return null
            return <MealGroup key={meal.id} label={meal.label} items={items} />
          })}
        </div>
      </Card>
      <SaveDayCard date={today} saved={(saved.data?.days ?? []).includes(today)} hasFood={report.data.food_log_count > 0} />
      {nutrition.data.configured ? <ExerciseCard nutrition={nutrition.data} activities={dayActivities} /> : null}
      <Micronutrients items={report.data.micronutrients} />
    </div>
  )
}

const macroKeys = { Protein: "protein", Carbohydrates: "carbs", Fat: "fat" } as const

function targetFor(name: string, calories: number | null, grams: ReturnType<typeof macroGramTargets> | null): number | null {
  if (name === "Calories") return calories
  const key = macroKeys[name as keyof typeof macroKeys]
  return key && grams ? grams[key] : null
}

function targetText(name: string, target: number | null, fallback: string): string {
  if (target == null) return fallback
  return name === "Calories" ? formatKcal(target) : formatGrams(target)
}

function MealGroup({ label, items }: { label: string; items: FoodLog[] }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [pendingId, setPendingId] = useState<number | null>(null)

  async function remove(id: number) {
    setPendingId(id)
    try {
      await deleteFoodLog(id)
      await queryClient.invalidateQueries({ queryKey: ["food-logs"] })
      await queryClient.invalidateQueries({ queryKey: ["reports"] })
      await queryClient.invalidateQueries({ queryKey: ["foods", "frequent"] })
    } catch (error) {
      toast.push(error instanceof ApiError ? error.message : "The log could not be removed.", "danger")
    } finally {
      setPendingId(null)
    }
  }

  return (
    <section>
      <h3 className="text-sm font-semibold text-muted">{label}</h3>
      <ul className="mt-2 space-y-2">
        {items.map((log) => {
          const calories = log.nutrients.find((item) => item.unit.toLowerCase() === "kcal" && item.name.toLowerCase().startsWith("energy"))
          return (
            <li key={log.id} className="flex items-center justify-between gap-3 rounded-2xl border border-line px-3 py-2">
              <span>
                <span className="block font-semibold">{log.food_name}</span>
                <span className="text-sm text-muted">{formatGrams(log.grams)}{calories ? ` · ${Math.round(calories.eaten)} kcal` : ""}</span>
              </span>
              <Button size="sm" variant="ghost" disabled={pendingId === log.id || log.id < 0} onClick={() => void remove(log.id)}>Remove</Button>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

function SaveDayCard({ date, saved, hasFood }: { date: string; saved: boolean; hasFood: boolean }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [pending, setPending] = useState(false)

  async function save() {
    setPending(true)
    try {
      await saveDay(date)
      await queryClient.invalidateQueries({ queryKey: ["days"] })
      toast.push("Day saved.")
    } catch (error) {
      toast.push(error instanceof ApiError ? error.message : "The day could not be saved.", "danger")
    } finally {
      setPending(false)
    }
  }

  return (
    <Card>
      <h2 className="font-display text-xl font-medium">Save this day</h2>
      <p className="mt-2 text-sm text-muted">Saved days are listed on Weekly. The API keeps a day after it has at least one food log.</p>
      <Button className="mt-4" disabled={pending || saved || !hasFood} onClick={() => void save()}>
        {saved ? "Day saved" : pending ? "Saving…" : "Save day"}
      </Button>
    </Card>
  )
}

function ExerciseCard({
  nutrition,
  activities,
}: {
  nutrition: Extract<NutritionGoals, { configured: true }>
  activities: Array<{ id: number; activity: string; duration_minutes: number | null; calories_burned: number | null }>
}) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const ready = nutrition.height_cm != null && nutrition.weight_kg != null
  const form = useForm<ActivityInput>({
    resolver: zodResolver(activitySchema),
    defaultValues: { activity: "", activity_type: "walking", duration_minutes: "", extra: false },
  })
  const mutation = useMutation({
    mutationFn: (values: ActivityInput) => createActivityLog({
      activity: values.activity,
      activity_type: values.activity_type,
      duration_minutes: Number(values.duration_minutes),
      weight_kg: nutrition.weight_kg ?? 0,
      height_cm: nutrition.height_cm ?? 0,
      extra: values.extra,
    }),
    onSuccess: async () => {
      form.reset({ activity: "", activity_type: "walking", duration_minutes: "", extra: false })
      await queryClient.invalidateQueries({ queryKey: ["activity-logs"] })
      await queryClient.invalidateQueries({ queryKey: ["reports"] })
      toast.push("Exercise logged.")
    },
    onError: (error) => {
      toast.push(error instanceof ApiError ? error.message : "Exercise could not be logged.", "danger")
    },
  })

  async function remove(id: number) {
    try {
      await deleteActivityLog(id)
      await queryClient.invalidateQueries({ queryKey: ["activity-logs"] })
      await queryClient.invalidateQueries({ queryKey: ["reports"] })
    } catch (error) {
      toast.push(error instanceof ApiError ? error.message : "Exercise could not be removed.", "danger")
    }
  }

  return (
    <Card>
      <h2 className="font-display text-xl font-medium">Exercise</h2>
      {ready ? (
        <form className="mt-4 space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))} noValidate>
          <Input label="Activity" error={form.formState.errors.activity?.message} {...form.register("activity")} />
          <Select label="Type" options={activityTypes} error={form.formState.errors.activity_type?.message} {...form.register("activity_type")} />
          <Input label="Minutes" inputMode="decimal" error={form.formState.errors.duration_minutes?.message} {...form.register("duration_minutes")} />
          <label className="flex items-start gap-3 text-sm">
            <input type="checkbox" className="mt-1" {...form.register("extra")} />
            <span>Count the active calories toward today's target. A fixed care-plan calorie number cannot take this credit.</span>
          </label>
          <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? "Saving…" : "Log exercise"}</Button>
        </form>
      ) : (
        <p className="mt-2 text-sm text-muted">Add height and weight in Settings before logging exercise.</p>
      )}
      <ul className="mt-4 space-y-2">
        {activities.map((log) => (
          <li key={log.id} className="flex items-center justify-between gap-3 text-sm">
            <span>{log.activity} · {log.duration_minutes ?? "—"} min{log.calories_burned == null ? "" : ` · ${formatKcal(log.calories_burned)}`}</span>
            <Button size="sm" variant="ghost" onClick={() => void remove(log.id)}>Remove</Button>
          </li>
        ))}
      </ul>
    </Card>
  )
}

function Micronutrients({ items }: { items: Array<{ name: string; unit: string; logged: number | null; target: number; percent: number | null; bar_width: number; limit: boolean; partial: boolean }> }) {
  if (items.length === 0) return null
  return (
    <Card>
      <details>
        <summary className="cursor-pointer font-display text-xl font-medium">Micronutrients</summary>
        <div className="mt-4 space-y-4">
          {items.map((item) => (
            <ProgressBar
              key={item.name}
              label={item.name}
              value={item.bar_width}
              tone={intakeTone(item.percent, item.limit)}
              detail={`${item.logged ?? 0} / ${item.target} ${item.unit}${item.partial ? " · partial" : ""}`}
            />
          ))}
        </div>
      </details>
    </Card>
  )
}
