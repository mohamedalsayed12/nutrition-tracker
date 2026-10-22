import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState, type ReactNode } from "react"
import { useForm } from "react-hook-form"
import { Link, Navigate } from "react-router-dom"
import { z } from "zod"
import { ApiError } from "../api/client.ts"
import { createActivityLog, deleteActivityLog, listRecentActivityLogs } from "../api/activityLogs.ts"
import { deleteFoodLog, listRecentFoodLogs } from "../api/foodLogs.ts"
import { getDailyReport, getSavedDays, saveDay } from "../api/reports.ts"
import { getHealthSettings, getMacroSplit, saveHealthSettings } from "../api/settings.ts"
import { Button } from "../components/ui/Button.tsx"
import { Card } from "../components/ui/Card.tsx"
import { EmptyState } from "../components/ui/EmptyState.tsx"
import { Input } from "../components/ui/Input.tsx"
import { ProgressBar } from "../components/ui/ProgressBar.tsx"
import { ProgressRing } from "../components/ui/ProgressRing.tsx"
import { Select } from "../components/ui/Select.tsx"
import { Skeleton } from "../components/ui/Skeleton.tsx"
import { useToast } from "../components/ui/Toast.tsx"
import { useNutrition } from "../hooks/useNutrition.ts"
import { addDays, browserTimeZone, formatDiaryDate, isSameLocalDay, localDateISO } from "../lib/dates.ts"
import { formatGrams, formatKcal } from "../lib/format.ts"
import { macroGramTargets } from "../lib/macroSplit.ts"
import { mealOptions } from "../lib/meals.ts"
import { intakeTone } from "../lib/progressTone.ts"
import type { ActivityType, FoodLog, HealthCondition, HealthSettings, IronAbsorptionCheck, NutritionGoals } from "../types/api.ts"

const conditionChoices: Array<{ value: HealthCondition; label: string; detail: string }> = [
  { value: "pregnancy", label: "Pregnant", detail: "Uses pregnancy reference targets. Periods cannot be selected at the same time." },
  { value: "diabetes", label: "Diabetes", detail: "Keeps the usual targets and shows the diabetes note." },
  { value: "ibs", label: "IBS", detail: "Keeps the usual targets and shows nutrients a restricted diet can miss." },
  { value: "menstruation", label: "Periods", detail: "Raises iron to the menstrual reference and raises vitamin C, which helps the body absorb iron." },
]

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
  const nutrition = useNutrition()
  const zone = browserTimeZone()
  const [today] = useState(() => localDateISO(new Date(), browserTimeZone()))
  const [day, setDay] = useState(today)
  const report = useQuery({ queryKey: ["reports", "daily", day, zone], queryFn: () => getDailyReport(day, zone) })
  const logs = useQuery({ queryKey: ["food-logs", "recent"], queryFn: listRecentFoodLogs })
  const activities = useQuery({ queryKey: ["activity-logs", "recent"], queryFn: listRecentActivityLogs })
  const saved = useQuery({ queryKey: ["days"], queryFn: getSavedDays })
  const macros = useQuery({ queryKey: ["settings", "macros"], queryFn: getMacroSplit })
  const health = useQuery({ queryKey: ["settings", "health"], queryFn: getHealthSettings })

  if (nutrition.isLoading || report.isLoading || macros.isLoading || health.isLoading) {
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

  const dayLogs = (logs.data ?? []).filter((log) => isSameLocalDay(log.logged_at, day, zone))
  const dayActivities = (activities.data ?? []).filter((log) => isSameLocalDay(log.logged_at, day, zone))
  const consumed = report.data.totals.Calories
  const burned = dayActivities.reduce((sum, log) => sum + (log.calories_burned ?? 0), 0)
  const goal = report.data.calorie_goal
  const remaining = goal == null ? null : goal - consumed
  const grams = goal == null ? null : macroGramTargets(goal, macros.data ?? { carbs_percent: 55, protein_percent: 20, fat_percent: 25 }, {
    carbs: health.data?.custom_carbs ?? null,
    protein: health.data?.custom_protein ?? null,
    fat: health.data?.custom_fat ?? null,
  })
  const macroBars = report.data.progress.filter((item) => item.name !== "Calories")

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => setDay((current) => addDays(current, -1))} aria-label="Previous day">Previous</Button>
          <h1 className="font-display text-xl font-medium sm:text-2xl">{formatDiaryDate(day)}</h1>
          <Button variant="secondary" size="sm" onClick={() => setDay((current) => addDays(current, 1))} aria-label="Next day">Next</Button>
        </div>
        <div className="flex items-center gap-2">
          {day !== today ? <Button variant="ghost" size="sm" onClick={() => setDay(today)}>Today</Button> : null}
          <SaveDayButton date={day} saved={(saved.data?.days ?? []).includes(day)} hasFood={report.data.food_log_count > 0} />
        </div>
      </div>

      <section className="rounded-2xl border border-line bg-card px-4 py-5">
        <h2 className="font-display text-lg font-medium">Energy summary</h2>
        <div className="mt-4 grid grid-cols-3 justify-items-center gap-2">
          <EnergyCircle label="Consumed" value={consumed} max={goal ?? consumed} tone={goal == null || goal <= 0 ? "accent" : intakeTone((consumed / goal) * 100)} />
          <EnergyCircle label="Burned" value={burned} max={Math.max(burned, goal ?? 0)} tone="accent" />
          <EnergyCircle
            label={remaining != null && remaining < 0 ? "Over" : "Remaining"}
            value={remaining == null ? 0 : Math.abs(remaining)}
            max={goal ?? 0}
            tone={remaining != null && remaining < 0 ? "danger" : "accent"}
          />
        </div>
        {report.data.exercise_credit > 0 ? <p className="mt-3 text-center text-sm text-muted">Remaining includes {formatKcal(report.data.exercise_credit)} from extra exercise.</p> : null}
      </section>

      <section className="rounded-2xl border border-line bg-card px-4 py-5">
        <h2 className="font-display text-lg font-medium">Macronutrient targets</h2>
        <div className="mt-4 space-y-4">
          {macroBars.length === 0 ? <p className="text-sm text-muted">Save a calorie target to see progress.</p> : macroBars.map((item) => {
            const target = targetFor(item.name, goal, grams)
            const amount = item.logged ?? 0
            const percent = target != null && target > 0 ? (amount / target) * 100 : null
            return (
              <ProgressBar
                key={item.name}
                label={item.name}
                value={percent ?? 0}
                tone={intakeTone(percent)}
                detail={`${amount} ${item.unit} · ${targetText(item.name, target, item.target_label)}`}
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
        </div>
      </section>

      <Micronutrients items={report.data.micronutrients} />

      <section className="overflow-hidden rounded-2xl border border-line bg-card">
        <div className="flex gap-2 border-b border-line px-4 py-3">
          <Link className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white" to="/add">+ Food</Link>
          <a className="rounded-full border border-line px-4 py-2 text-sm font-semibold" href="#exercise">+ Exercise</a>
        </div>
        {logs.isError ? <p className="px-4 py-3 text-sm text-danger">Meals could not be loaded.</p> : null}
        {logs.isLoading ? <Skeleton className="m-4 h-24" /> : mealOptions.map((meal) => {
          const items = dayLogs.filter((log) => log.meal === meal.id)
          const subtotal = items.reduce((sum, log) => sum + (foodKcal(log) ?? 0), 0)
          const ironCheck = report.data?.iron_absorption?.find((check) => check.meal === meal.id)
          return (
            <DiaryGroup
              key={meal.id}
              title={meal.id === "snack" ? "Snacks" : meal.label}
              subtotal={items.length === 0 ? "" : formatKcal(subtotal)}
              addTo={`/add?meal=${meal.id}`}
              addLabel="Add Food"
              ironCheck={ironCheck}
            >
              {items.map((log) => <FoodRow key={log.id} log={log} />)}
            </DiaryGroup>
          )
        })}
        <ExerciseGroup activities={dayActivities} burned={burned} nutrition={nutrition.data?.configured ? nutrition.data : null} />
        {health.data ? <ConditionsGroup key={`${health.data.conditions.join("|")}:${health.data.trimester ?? ""}`} settings={health.data} /> : null}
      </section>
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

function foodKcal(log: FoodLog): number | null {
  const calories = log.nutrients.find((item) => item.unit.toLowerCase() === "kcal" && item.name.toLowerCase().startsWith("energy"))
  return calories ? Math.round(calories.eaten) : null
}

function EnergyCircle({ label, value, max, tone }: { label: string; value: number; max: number; tone: "accent" | "amber" | "danger" }) {
  return (
    <figure className="flex flex-col items-center gap-2">
      <ProgressRing size="sm" value={value} max={max} label={label} tone={tone} />
      <figcaption className="text-sm font-semibold">{label}</figcaption>
    </figure>
  )
}

function DiaryGroup({ title, subtotal, addTo, addLabel, ironCheck, children }: { title: string; subtotal: string; addTo: string; addLabel: string; ironCheck?: IronAbsorptionCheck; children: ReactNode }) {
  return (
    <section className="border-b border-line">
      <div className="flex items-center justify-between bg-canvas px-4 py-2">
        <h2 className="text-sm font-semibold">{title}</h2>
        <span className="text-sm tabular-nums text-muted">{subtotal}</span>
      </div>
      <ul>{children}</ul>
      {ironCheck ? <IronTip check={ironCheck} /> : null}
      <Link className="block px-4 py-2 text-sm font-semibold text-accent hover:underline" to={addTo}>+ {addLabel}</Link>
    </section>
  )
}

/**
 * Shows when a meal has iron but little vitamin C. Vitamin C only helps iron
 * absorption when it is eaten in the same meal, so this is checked per meal.
 * A meal that already pairs them is only mentioned when periods are selected.
 */
function IronTip({ check }: { check: IronAbsorptionCheck }) {
  if (check.status === "good" && !check.highlight) return null
  const needsVitaminC = check.status === "add_vitamin_c"
  const colour = needsVitaminC ? (check.highlight ? "text-amber font-semibold" : "text-amber") : "text-accent"
  return (
    <p role="note" className={`mx-4 mb-2 rounded-lg bg-canvas px-3 py-2 text-sm ${colour}`}>
      <span className="font-semibold">{needsVitaminC ? "Iron tip: " : "Iron + vitamin C: "}</span>
      {check.tip}
    </p>
  )
}

function FoodRow({ log }: { log: FoodLog }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [pending, setPending] = useState(false)
  const calories = foodKcal(log)

  async function remove() {
    setPending(true)
    try {
      await deleteFoodLog(log.id)
      await queryClient.invalidateQueries({ queryKey: ["food-logs"] })
      await queryClient.invalidateQueries({ queryKey: ["reports"] })
      await queryClient.invalidateQueries({ queryKey: ["foods", "frequent"] })
    } catch (error) {
      toast.push(error instanceof ApiError ? error.message : "The log could not be removed.", "danger")
    } finally {
      setPending(false)
    }
  }

  return (
    <li className="grid grid-cols-[1fr_auto_auto] items-center gap-3 border-t border-line px-4 py-2 text-sm">
      <span className="font-semibold">{log.food_name}</span>
      <span className="text-muted">{formatGrams(log.grams)}</span>
      <span className="flex items-center gap-2 tabular-nums">
        {calories == null ? "—" : calories}
        <Button size="sm" variant="ghost" disabled={pending || log.id < 0} onClick={() => void remove()}>Remove</Button>
      </span>
    </li>
  )
}

function ExerciseGroup({
  activities,
  burned,
  nutrition,
}: {
  activities: Array<{ id: number; activity: string; duration_minutes: number | null; calories_burned: number | null }>
  burned: number
  nutrition: Extract<NutritionGoals, { configured: true }> | null
}) {
  const [open, setOpen] = useState(false)
  return (
    <section id="exercise">
      <div className="flex items-center justify-between bg-canvas px-4 py-2">
        <h2 className="text-sm font-semibold">Exercise</h2>
        <span className="text-sm tabular-nums text-muted">{activities.length === 0 ? "" : formatKcal(burned)}</span>
      </div>
      <ul>
        {activities.map((log) => <ExerciseRow key={log.id} log={log} />)}
      </ul>
      <button type="button" className="block px-4 py-2 text-sm font-semibold text-accent hover:underline" onClick={() => setOpen((current) => !current)}>
        + Add Exercise
      </button>
      {open && nutrition ? <div className="border-t border-line px-4 py-4"><ExerciseCard nutrition={nutrition} plain /></div> : null}
    </section>
  )
}

function ExerciseRow({ log }: { log: { id: number; activity: string; duration_minutes: number | null; calories_burned: number | null } }) {
  const queryClient = useQueryClient()
  const toast = useToast()

  async function remove() {
    try {
      await deleteActivityLog(log.id)
      await queryClient.invalidateQueries({ queryKey: ["activity-logs"] })
      await queryClient.invalidateQueries({ queryKey: ["reports"] })
    } catch (error) {
      toast.push(error instanceof ApiError ? error.message : "Exercise could not be removed.", "danger")
    }
  }

  return (
    <li className="grid grid-cols-[1fr_auto_auto] items-center gap-3 border-t border-line px-4 py-2 text-sm">
      <span className="font-semibold">{log.activity}</span>
      <span className="text-muted">{log.duration_minutes ?? "—"} min</span>
      <span className="flex items-center gap-2 tabular-nums">
        {log.calories_burned == null ? "—" : Math.round(log.calories_burned)}
        <Button size="sm" variant="ghost" onClick={() => void remove()}>Remove</Button>
      </span>
    </li>
  )
}

function SaveDayButton({ date, saved, hasFood }: { date: string; saved: boolean; hasFood: boolean }) {
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
    <Button variant="secondary" size="sm" disabled={pending || saved || !hasFood} onClick={() => void save()}>
      {saved ? "Day saved" : pending ? "Saving…" : "Save day"}
    </Button>
  )
}

function ExerciseCard({
  nutrition,
  plain = false,
}: {
  nutrition: Extract<NutritionGoals, { configured: true }>
  plain?: boolean
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

  const formBody = ready ? (
    <form className="space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))} noValidate>
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
    <p className="text-sm text-muted">Add height and weight in Settings before logging exercise.</p>
  )
  return plain ? formBody : <Card><h2 className="font-display text-xl font-medium">Exercise</h2>{formBody}</Card>
}

function ConditionsGroup({ settings }: { settings: HealthSettings }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [pending, setPending] = useState(false)
  const [conditions, setConditions] = useState<HealthCondition[]>(settings.conditions)
  const [trimester, setTrimester] = useState<1 | 2 | 3 | null>(settings.trimester)
  const [adding, setAdding] = useState(false)
  const selected = conditionChoices.filter((choice) => conditions.includes(choice.value))
  const available = conditionChoices.filter((choice) => !conditions.includes(choice.value))

  async function persist(nextConditions: HealthCondition[], nextTrimester: 1 | 2 | 3 | null) {
    setConditions(nextConditions)
    setTrimester(nextTrimester)
    setPending(true)
    try {
      const saved = await saveHealthSettings({
        conditions: nextConditions,
        trimester: nextConditions.includes("pregnancy") ? nextTrimester : null,
        custom_calories: settings.custom_calories,
        custom_carbs: settings.custom_carbs,
        custom_protein: settings.custom_protein,
        custom_fat: settings.custom_fat,
        micronutrient_overrides: settings.micronutrient_overrides,
      })
      queryClient.setQueryData(["settings", "health"], saved)
      await queryClient.invalidateQueries({ queryKey: ["reports"] })
      await queryClient.invalidateQueries({ queryKey: ["goals"] })
    } catch (error) {
      setConditions(settings.conditions)
      setTrimester(settings.trimester)
      toast.push(error instanceof ApiError ? error.message : "The condition could not be saved.", "danger")
    } finally {
      setPending(false)
    }
  }

  function add(condition: HealthCondition) {
    const next = new Set(conditions)
    let nextTrimester = trimester
    next.add(condition)
    if (condition === "pregnancy") {
      next.delete("menstruation")
      nextTrimester = nextTrimester ?? 1
    }
    if (condition === "menstruation") {
      next.delete("pregnancy")
      nextTrimester = null
    }
    setAdding(false)
    void persist([...next], nextTrimester)
  }

  function remove(condition: HealthCondition) {
    const next = conditions.filter((item) => item !== condition)
    void persist(next, condition === "pregnancy" ? null : trimester)
  }

  return (
    <section>
      <div className="flex items-center justify-between bg-canvas px-4 py-2">
        <h2 className="text-sm font-semibold">Conditions</h2>
        <span className="text-sm tabular-nums text-muted">{selected.length === 0 ? "" : selected.length}</span>
      </div>
      <ul>
        {selected.map((choice) => (
          <li key={choice.value} className="grid grid-cols-[1fr_auto] items-center gap-3 border-t border-line px-4 py-2 text-sm">
            <span>
              <span className="block font-semibold">{choice.label}</span>
              <span className="text-muted">{choice.value === "pregnancy" ? `Trimester ${trimester ?? 1}` : choice.detail}</span>
            </span>
            <Button size="sm" variant="ghost" disabled={pending} onClick={() => remove(choice.value)}>Remove</Button>
          </li>
        ))}
        {conditions.includes("pregnancy") ? (
          <li className="border-t border-line px-4 py-3">
            <Select
              label="Pregnancy trimester"
              value={String(trimester ?? 1)}
              options={[{ value: "1", label: "First" }, { value: "2", label: "Second" }, { value: "3", label: "Third" }]}
              onChange={(event) => void persist(conditions, Number(event.target.value) as 1 | 2 | 3)}
            />
          </li>
        ) : null}
        {adding ? available.map((choice) => (
          <li key={choice.value} className="grid grid-cols-[1fr_auto] items-center gap-3 border-t border-line px-4 py-2 text-sm">
            <span>
              <span className="block font-semibold">{choice.label}</span>
              <span className="text-muted">{choice.detail}</span>
            </span>
            <Button size="sm" disabled={pending} onClick={() => add(choice.value)}>Add</Button>
          </li>
        )) : null}
        {adding && available.length === 0 ? <li className="border-t border-line px-4 py-2 text-sm text-muted">Every condition is already added.</li> : null}
      </ul>
      <button type="button" className="block px-4 py-2 text-sm font-semibold text-accent hover:underline" onClick={() => setAdding((current) => !current)}>
        + Add condition
      </button>
    </section>
  )
}

type MicronutrientItem = { name: string; unit: string; logged: number | null; target: number; percent: number | null; bar_width: number; limit: boolean; partial: boolean }

// The ones most people are short of (or over, for sodium), shown when the section is opened.
const KEY_NUTRIENTS = ["Vitamin D", "Vitamin C", "Vitamin B12", "Iron", "Calcium", "Magnesium", "Potassium", "Sodium"]
const VITAMIN_PREFIXES = ["Vitamin", "Thiamin", "Riboflavin", "Niacin", "Pantothenic", "Biotin", "Folate", "Choline"]
const MICRO_VIEW_KEY = "nutrition.micronutrients_view"
type MicroView = "closed" | "key" | "all"

function readMicroView(): MicroView {
  try {
    const saved = localStorage.getItem(MICRO_VIEW_KEY)
    return saved === "key" || saved === "all" ? saved : "closed"
  } catch {
    return "closed"
  }
}

function Micronutrients({ items }: { items: MicronutrientItem[] }) {
  const [view, setViewState] = useState<MicroView>(readMicroView)
  if (items.length === 0) return null
  const setView = (next: MicroView) => {
    setViewState(next)
    try { localStorage.setItem(MICRO_VIEW_KEY, next) } catch { /* private mode */ }
  }
  const open = view !== "closed"
  const goals = items.filter((item) => !item.limit)
  const met = goals.filter((item) => (item.percent ?? 0) >= 100).length
  const key = KEY_NUTRIENTS.map((name) => items.find((item) => item.name === name)).filter((item): item is MicronutrientItem => item != null)
  const vitamins = items.filter((item) => VITAMIN_PREFIXES.some((prefix) => item.name.startsWith(prefix)))
  const minerals = items.filter((item) => !vitamins.includes(item))

  const bar = (item: MicronutrientItem) => (
    <ProgressBar
      key={item.name}
      label={item.limit ? `${item.name} (limit)` : item.name}
      value={item.bar_width}
      tone={intakeTone(item.percent, item.limit)}
      detail={`${item.logged ?? 0} / ${item.target} ${item.unit}${item.partial ? " · partial" : ""}`}
    />
  )

  return (
    <section className="rounded-2xl border border-line bg-card px-4 py-5">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 text-left"
        aria-expanded={open}
        aria-controls="micronutrient-list"
        onClick={() => setView(open ? "closed" : "key")}
      >
        <span>
          <span className="block font-display text-lg font-medium">Vitamins and minerals</span>
          <span className="block text-sm text-muted">{met} of {goals.length} targets met today</span>
        </span>
        <ChevronDown className={open ? "rotate-180" : undefined} />
      </button>
      {open ? (
        <div id="micronutrient-list" className="mt-4">
          {view === "key" ? (
            <div className="space-y-4">{key.map(bar)}</div>
          ) : (
            <div className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">Vitamins</h3>
                {vitamins.map(bar)}
              </div>
              <div className="space-y-4">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">Minerals</h3>
                {minerals.map(bar)}
              </div>
            </div>
          )}
          <button
            type="button"
            className="mt-5 w-full rounded-2xl border border-line py-2.5 text-sm font-semibold text-accent hover:bg-canvas focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            onClick={() => setView(view === "all" ? "key" : "all")}
          >
            {view === "all" ? "Show key nutrients only" : `Show all ${items.length}`}
          </button>
        </div>
      ) : null}
    </section>
  )
}

function ChevronDown({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true" className={`h-5 w-5 shrink-0 transition-transform ${className ?? ""}`}>
      <path d="M5 7.5 10 12.5 15 7.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
