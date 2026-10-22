import { zodResolver } from "@hookform/resolvers/zod"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { Link, useNavigate } from "react-router-dom"
import { ApiError, fieldErrors } from "../api/client.ts"
import { getCalories, saveCalories, saveNutrition } from "../api/goals.ts"
import { getHealthSettings, getMacroSplit, resetMacroSplit, saveHealthSettings, saveMacroSplit } from "../api/settings.ts"
import { NutritionFields } from "../components/nutrition/NutritionFields.tsx"
import { GoalResults } from "../components/nutrition/GoalResults.tsx"
import { ThemeToggle } from "../components/ThemeToggle.tsx"
import { Button } from "../components/ui/Button.tsx"
import { Card } from "../components/ui/Card.tsx"
import { EmptyState } from "../components/ui/EmptyState.tsx"
import { Input } from "../components/ui/Input.tsx"
import { Select } from "../components/ui/Select.tsx"
import { Skeleton } from "../components/ui/Skeleton.tsx"
import { useToast } from "../components/ui/Toast.tsx"
import { useCurrentUser } from "../hooks/useCurrentUser.ts"
import { useNutrition } from "../hooks/useNutrition.ts"
import { clearToken } from "../lib/auth.ts"
import { formatGrams, formatKcal } from "../lib/format.ts"
import { adjustMacroSplit, normalizeMacroSplit, type MacroPercents } from "../lib/macroSplit.ts"
import { cn } from "../lib/cn.ts"
import {
  calorieSchema,
  healthSchema,
  nutritionSchema,
  readNumber,
  readOptionalNumber,
  type CalorieInput,
  type HealthInput,
  type NutritionInput,
} from "../lib/schemas.ts"
import type { HealthCondition, HealthSettings, NutritionGoals, NutritionSetupResponse } from "../types/api.ts"

const conditionChoices: Array<{ value: HealthCondition; label: string; detail: string }> = [
  { value: "pregnancy", label: "Pregnant", detail: "Uses pregnancy reference targets. Periods cannot be selected at the same time." },
  { value: "diabetes", label: "Diabetes", detail: "Shows the diabetes note returned by the API." },
  { value: "ibs", label: "IBS", detail: "Shows the IBS note returned by the API." },
  { value: "menstruation", label: "Periods", detail: "Raises iron to the menstrual reference and raises vitamin C, which helps the body absorb iron." },
]

const macroLabels: Array<{ key: keyof MacroPercents; label: string }> = [
  { key: "carbs_percent", label: "Carbohydrates" },
  { key: "protein_percent", label: "Protein" },
  { key: "fat_percent", label: "Fat" },
]

function nutritionDefaults(nutrition: NutritionGoals): NutritionInput {
  if (!nutrition.configured) {
    return { age: "", sex: "male", height_cm: "", weight_kg: "", activity_level: "moderately active", goal: "maintain" }
  }
  return {
    age: String(nutrition.age),
    sex: nutrition.sex,
    height_cm: nutrition.height_cm == null ? "" : String(nutrition.height_cm),
    weight_kg: nutrition.weight_kg == null ? "" : String(nutrition.weight_kg),
    activity_level: nutrition.activity_level ?? "moderately active",
    goal: "maintain",
  }
}

function healthDefaults(settings: HealthSettings): HealthInput {
  return {
    conditions: settings.conditions,
    trimester: settings.trimester == null ? "" : String(settings.trimester) as HealthInput["trimester"],
    custom_calories: settings.custom_calories == null ? "" : String(settings.custom_calories),
    custom_carbs: settings.custom_carbs == null ? "" : String(settings.custom_carbs),
    custom_protein: settings.custom_protein == null ? "" : String(settings.custom_protein),
    custom_fat: settings.custom_fat == null ? "" : String(settings.custom_fat),
  }
}

function report(error: unknown, push: (message: string, tone?: "info" | "danger") => void, fallback: string) {
  push(error instanceof ApiError ? error.message : fallback, "danger")
}

export function SettingsPage() {
  const user = useCurrentUser()
  const nutrition = useNutrition()
  const calories = useQuery({ queryKey: ["goals", "calories"], queryFn: getCalories })
  const macros = useQuery({ queryKey: ["settings", "macros"], queryFn: getMacroSplit })
  const health = useQuery({ queryKey: ["settings", "health"], queryFn: getHealthSettings })
  const loading = user.isLoading || nutrition.isLoading || calories.isLoading || macros.isLoading || health.isLoading
  const failed = user.isError || nutrition.isError || calories.isError || macros.isError || health.isError

  if (loading) {
    return (
      <div className="space-y-4" aria-busy="true" aria-live="polite">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-36 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (failed || !user.data || !nutrition.data || !calories.data || !macros.data || !health.data) {
    return (
      <EmptyState
        title="Couldn't load settings"
        body="One of the settings requests failed. Check that the API is running, then try again."
        action={(
          <Button onClick={() => {
            void user.refetch()
            void nutrition.refetch()
            void calories.refetch()
            void macros.refetch()
            void health.refetch()
          }}
          >
            Retry
          </Button>
        )}
      />
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="font-display text-3xl font-medium">Settings</h1>
      <ProfileCard name={user.data.name} email={user.data.email} />
      <Card>
        <h2 className="font-display text-xl font-medium">Appearance</h2>
        <p className="mt-2 text-sm text-muted">Light is the default. Dark mode stays on this browser.</p>
        <div className="mt-4"><ThemeToggle /></div>
      </Card>
      <NutritionCard nutrition={nutrition.data} />
      <CalorieCard key={calories.data.calories ?? "none"} calories={calories.data.calories} />
      <MacroCard key={`${macros.data.carbs_percent}-${macros.data.protein_percent}-${macros.data.fat_percent}-${macros.data.configured}`} initial={normalizeMacroSplit(macros.data)} configured={nutrition.data.configured} />
      <HealthCard key={JSON.stringify(health.data)} settings={health.data} configured={nutrition.data.configured} />
    </div>
  )
}

function ProfileCard({ name, email }: { name: string; email: string }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  return (
    <Card>
      <h2 className="font-display text-xl font-medium">Profile</h2>
      <p className="mt-3 font-semibold">{name}</p>
      <p className="text-sm text-muted">{email}</p>
      <Button
        className="mt-4"
        variant="secondary"
        onClick={() => {
          clearToken()
          queryClient.clear()
          navigate("/login", { replace: true })
        }}
      >
        Sign out
      </Button>
    </Card>
  )
}

function NutritionCard({ nutrition }: { nutrition: NutritionGoals }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [pending, setPending] = useState(false)
  const [result, setResult] = useState<NutritionSetupResponse | null>(null)
  const form = useForm<NutritionInput>({ resolver: zodResolver(nutritionSchema), defaultValues: nutritionDefaults(nutrition) })

  async function onSubmit(values: NutritionInput) {
    setPending(true)
    try {
      const saved = await saveNutrition({
        age: readNumber(values.age),
        sex: values.sex,
        height_cm: readNumber(values.height_cm),
        weight_kg: readNumber(values.weight_kg),
        activity_level: values.activity_level,
        goal: values.goal,
      })
      setResult(saved)
      await queryClient.invalidateQueries({ queryKey: ["goals"] })
      await queryClient.invalidateQueries({ queryKey: ["settings", "health"] })
      toast.push("Targets updated.")
    } catch (error) {
      report(error, toast.push, "Targets could not be saved.")
      for (const [field, message] of Object.entries(fieldErrors(error))) {
        if (field in values) form.setError(field as keyof NutritionInput, { message })
      }
    } finally {
      setPending(false)
    }
  }

  return (
    <Card>
      <h2 className="font-display text-xl font-medium">Body and goal</h2>
      <p className="mt-2 text-sm text-muted">
        {nutrition.configured
          ? `Current protein range is ${formatGrams(nutrition.protein_min)} to ${formatGrams(nutrition.protein_max)}. Carbohydrates are ${formatGrams(nutrition.carbs)}.`
          : "Goals are not saved yet. You can use the step-by-step setup or save them here."}
      </p>
      {!nutrition.configured ? (
        <Link className="mt-3 inline-block text-sm font-semibold text-accent underline-offset-4 hover:underline" to="/onboarding">Open the setup wizard</Link>
      ) : null}
      <form className="mt-5" onSubmit={form.handleSubmit(onSubmit)} noValidate>
        <NutritionFields form={form} part="all" />
        <Button className="mt-5" type="submit" disabled={pending}>{pending ? "Saving…" : "Recalculate targets"}</Button>
      </form>
      {result ? <div className="mt-6 border-t border-line pt-5"><GoalResults result={result} /></div> : null}
    </Card>
  )
}

function CalorieCard({ calories }: { calories: number | null }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [pending, setPending] = useState(false)
  const form = useForm<CalorieInput>({
    resolver: zodResolver(calorieSchema),
    defaultValues: { calories: calories == null ? "" : String(calories) },
  })

  async function onSubmit(values: CalorieInput) {
    setPending(true)
    try {
      await saveCalories({ calories: readNumber(values.calories) })
      await queryClient.invalidateQueries({ queryKey: ["goals"] })
      await queryClient.invalidateQueries({ queryKey: ["settings", "health"] })
      toast.push("Daily target saved.")
    } catch (error) {
      report(error, toast.push, "The calorie target could not be saved.")
      const fields = fieldErrors(error)
      if (fields.calories) form.setError("calories", { message: fields.calories })
    } finally {
      setPending(false)
    }
  }

  return (
    <Card>
      <h2 className="font-display text-xl font-medium">Daily calorie target</h2>
      <p className="mt-2 text-sm text-muted">
        {calories == null ? "No target is saved yet." : `Saved target: ${formatKcal(calories)}.`}
        {" "}Once health settings exist, saving here also writes the care-plan calorie number.
      </p>
      <form className="mt-4 space-y-4" onSubmit={form.handleSubmit(onSubmit)} noValidate>
        <Input label="Calories" inputMode="decimal" hint="From 500 to 10,000." error={form.formState.errors.calories?.message} {...form.register("calories")} />
        <Button type="submit" disabled={pending}>{pending ? "Saving…" : "Save target"}</Button>
      </form>
    </Card>
  )
}

function MacroCard({ initial, configured }: { initial: MacroPercents; configured: boolean }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [split, setSplit] = useState(initial)
  const [pending, setPending] = useState(false)
  const total = split.carbs_percent + split.protein_percent + split.fat_percent

  async function save() {
    setPending(true)
    try {
      const saved = await saveMacroSplit(split)
      const next = normalizeMacroSplit(saved)
      setSplit(next)
      queryClient.setQueryData(["settings", "macros"], { configured: true, ...next })
      toast.push("Macro split saved.")
    } catch (error) {
      report(error, toast.push, "The macro split could not be saved.")
    } finally {
      setPending(false)
    }
  }

  async function reset() {
    setPending(true)
    try {
      await resetMacroSplit()
      const next = normalizeMacroSplit({ carbs_percent: 55, protein_percent: 20, fat_percent: 25 })
      setSplit(next)
      queryClient.setQueryData(["settings", "macros"], { configured: false, ...next })
      toast.push("Macro split reset to 55 / 20 / 25.")
    } catch (error) {
      report(error, toast.push, "The macro split could not be reset.")
    } finally {
      setPending(false)
    }
  }

  return (
    <Card>
      <h2 className="font-display text-xl font-medium">Macro split</h2>
      <p className="mt-2 text-sm text-muted">Moving one slider keeps the three shares at 100. The default is 55% carbohydrates, 20% protein, and 25% fat.</p>
      <div className="mt-4 space-y-4">
        {macroLabels.map((item) => (
          <label key={item.key} className="block text-sm font-semibold">
            <span className="flex justify-between"><span>{item.label}</span><span>{split[item.key]}%</span></span>
            <input
              className="mt-2 w-full accent-accent"
              type="range"
              min={0}
              max={100}
              step={1}
              value={split[item.key]}
              aria-valuetext={`${split[item.key]} percent`}
              onChange={(event) => setSplit(adjustMacroSplit(split, item.key, Number(event.target.value)))}
            />
          </label>
        ))}
      </div>
      <p className="mt-3 text-sm font-semibold text-accent">Total {total}%</p>
      {!configured ? <p className="mt-2 text-sm text-muted">Save body and goal first. The API rejects a split until nutrition setup is complete.</p> : null}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button onClick={() => void save()} disabled={pending || !configured}>Save split</Button>
        <Button variant="secondary" onClick={() => void reset()} disabled={pending || !configured}>Reset</Button>
      </div>
    </Card>
  )
}

function HealthCard({ settings, configured }: { settings: HealthSettings; configured: boolean }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [pending, setPending] = useState(false)
  const form = useForm<HealthInput>({ resolver: zodResolver(healthSchema), defaultValues: healthDefaults(settings) })
  const selected = form.watch("conditions")
  const pregnant = selected.includes("pregnancy")
  const conditionError = form.formState.errors.conditions
  const conditionMessage = conditionError && "message" in conditionError ? conditionError.message : undefined

  function toggle(condition: HealthCondition) {
    const current = new Set(form.getValues("conditions"))
    if (current.has(condition)) {
      current.delete(condition)
      if (condition === "pregnancy") form.setValue("trimester", "", { shouldValidate: true })
    } else {
      current.add(condition)
      if (condition === "pregnancy") {
        current.delete("menstruation")
        if (!form.getValues("trimester")) form.setValue("trimester", "1")
      }
      if (condition === "menstruation") {
        current.delete("pregnancy")
        form.setValue("trimester", "")
      }
    }
    form.setValue("conditions", [...current], { shouldValidate: true, shouldDirty: true })
  }

  async function onSubmit(values: HealthInput) {
    setPending(true)
    try {
      const saved = await saveHealthSettings({
        conditions: values.conditions,
        trimester: values.conditions.includes("pregnancy") && values.trimester ? Number(values.trimester) as 1 | 2 | 3 : null,
        custom_calories: readOptionalNumber(values.custom_calories),
        custom_carbs: readOptionalNumber(values.custom_carbs),
        custom_protein: readOptionalNumber(values.custom_protein),
        custom_fat: readOptionalNumber(values.custom_fat),
        micronutrient_overrides: settings.micronutrient_overrides,
      })
      form.reset(healthDefaults(saved))
      queryClient.setQueryData(["settings", "health"], saved)
      await queryClient.invalidateQueries({ queryKey: ["goals"] })
      toast.push("Health settings saved.")
    } catch (error) {
      report(error, toast.push, "Health settings could not be saved.")
      for (const [field, message] of Object.entries(fieldErrors(error))) {
        if (field === "conditions" || field === "trimester" || field.startsWith("custom_")) {
          form.setError(field as keyof HealthInput, { message })
        }
      }
    } finally {
      setPending(false)
    }
  }

  return (
    <Card>
      <h2 className="font-display text-xl font-medium">Health</h2>
      <p className="mt-2 text-sm text-muted">Leave a custom amount blank to keep the calculated target. Saved micronutrient overrides are sent back unchanged.</p>
      {!configured ? <p className="mt-2 text-sm text-muted">Save body and goal first. The API rejects health settings until nutrition setup is complete.</p> : null}
      <form className="mt-4 space-y-4" onSubmit={form.handleSubmit(onSubmit)} noValidate>
        <fieldset>
          <legend className="text-sm font-semibold">Conditions</legend>
          <div className="mt-2 space-y-2">
            {conditionChoices.map((choice) => {
              const checked = selected.includes(choice.value)
              return (
                <label key={choice.value} className={cn("flex cursor-pointer gap-3 rounded-2xl border p-3", checked ? "border-accent bg-accent-soft" : "border-line")}>
                  <input type="checkbox" className="mt-1" checked={checked} onChange={() => toggle(choice.value)} />
                  <span>
                    <span className="block text-sm font-semibold">{choice.label}</span>
                    <span className="mt-1 block text-sm font-normal text-muted">{choice.detail}</span>
                  </span>
                </label>
              )
            })}
          </div>
          {conditionMessage ? <span className="mt-1 block text-sm text-danger">{conditionMessage}</span> : null}
        </fieldset>
        {pregnant ? (
          <Select
            label="Pregnancy trimester"
            error={form.formState.errors.trimester?.message}
            options={[
              { value: "1", label: "First" },
              { value: "2", label: "Second" },
              { value: "3", label: "Third" },
            ]}
            {...form.register("trimester")}
          />
        ) : null}
        <Input label="Care-plan calories" inputMode="decimal" hint="Optional. 500 to 10,000. This can replace the goal calories." error={form.formState.errors.custom_calories?.message} {...form.register("custom_calories")} />
        <Input label="Care-plan carbohydrates (g)" inputMode="decimal" hint="Optional. Greater than 0 and at most 1,500." error={form.formState.errors.custom_carbs?.message} {...form.register("custom_carbs")} />
        <Input label="Care-plan protein (g)" inputMode="decimal" hint="Optional. Greater than 0 and at most 1,500." error={form.formState.errors.custom_protein?.message} {...form.register("custom_protein")} />
        <Input label="Care-plan fat (g)" inputMode="decimal" hint="Optional. Greater than 0 and at most 1,500." error={form.formState.errors.custom_fat?.message} {...form.register("custom_fat")} />
        <Button type="submit" disabled={pending || !configured}>{pending ? "Saving…" : "Save health settings"}</Button>
      </form>
      {settings.guidance.length > 0 ? (
        <div className="mt-6 space-y-4 border-t border-line pt-5">
          {settings.guidance.map((profile) => (
            <article key={profile.label}>
              <h3 className="font-semibold">{profile.label}</h3>
              <p className="mt-1 text-sm text-muted">{profile.summary}</p>
              <ul className="mt-2 space-y-1 text-sm text-muted">
                {Object.entries(profile.nutrients).map(([name, note]) => <li key={name}><span className="font-semibold text-ink">{name}.</span> {note}</li>)}
              </ul>
              <a className="mt-2 inline-block text-sm font-semibold text-accent underline-offset-4 hover:underline" href={profile.source} target="_blank" rel="noreferrer">Source</a>
            </article>
          ))}
        </div>
      ) : null}
    </Card>
  )
}
