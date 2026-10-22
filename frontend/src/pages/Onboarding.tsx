import { zodResolver } from "@hookform/resolvers/zod"
import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { useNavigate } from "react-router-dom"
import { ApiError, fieldErrors } from "../api/client.ts"
import { saveNutrition } from "../api/goals.ts"
import { GoalResults } from "../components/nutrition/GoalResults.tsx"
import { NutritionFields } from "../components/nutrition/NutritionFields.tsx"
import { ThemeToggle } from "../components/ThemeToggle.tsx"
import { Button } from "../components/ui/Button.tsx"
import { Card } from "../components/ui/Card.tsx"
import { EmptyState } from "../components/ui/EmptyState.tsx"
import { Skeleton } from "../components/ui/Skeleton.tsx"
import { useToast } from "../components/ui/Toast.tsx"
import { useCurrentUser } from "../hooks/useCurrentUser.ts"
import { useNutrition } from "../hooks/useNutrition.ts"
import { clearToken } from "../lib/auth.ts"
import { nutritionSchema, readNumber, type NutritionInput } from "../lib/schemas.ts"
import type { NutritionGoals, NutritionSetupResponse } from "../types/api.ts"

const steps = [
  { title: "Your body", fields: ["age", "sex", "height_cm", "weight_kg"] },
  { title: "Usual activity", fields: ["activity_level"] },
  { title: "Goal", fields: ["goal"] },
] as const

function defaults(nutrition: NutritionGoals | undefined): NutritionInput {
  if (!nutrition?.configured) {
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

export function OnboardingPage() {
  const user = useCurrentUser()
  const nutrition = useNutrition()

  if (user.isLoading || nutrition.isLoading) {
    return (
      <main className="mx-auto w-full max-w-lg px-4 py-10" aria-busy="true">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="mt-6 h-80 w-full" />
      </main>
    )
  }

  if (user.isError || nutrition.isError || !user.data || !nutrition.data) {
    return (
      <main className="mx-auto w-full max-w-lg px-4 py-10">
        <EmptyState
          title="Couldn't load setup"
          body="Your account loaded the sign-in, but goals didn't come back."
          action={<Button onClick={() => { void user.refetch(); void nutrition.refetch() }}>Retry</Button>}
        />
      </main>
    )
  }

  return <Wizard name={user.data.name} nutrition={nutrition.data} />
}

function Wizard({ name, nutrition }: { name: string; nutrition: NutritionGoals }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const toast = useToast()
  const [step, setStep] = useState(0)
  const [pending, setPending] = useState(false)
  const [result, setResult] = useState<NutritionSetupResponse | null>(null)
  const form = useForm<NutritionInput>({ resolver: zodResolver(nutritionSchema), defaultValues: defaults(nutrition) })
  const current = steps[step]

  function signOut() {
    clearToken()
    queryClient.clear()
    navigate("/login", { replace: true })
  }

  async function next() {
    if (!current) return
    const valid = await form.trigger([...current.fields])
    if (!valid) return
    if (step < steps.length - 1) setStep(step + 1)
  }

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
      await queryClient.invalidateQueries({ queryKey: ["goals"] })
      setResult(saved)
      toast.push("Goals saved.")
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Goals could not be saved."
      toast.push(message, "danger")
      for (const [field, fieldMessage] of Object.entries(fieldErrors(error))) {
        if (field in values) {
          form.setError(field as keyof NutritionInput, { message: fieldMessage })
          const index = steps.findIndex((item) => (item.fields as readonly string[]).includes(field))
          if (index >= 0) setStep(index)
        }
      }
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-lg flex-col px-4 py-8">
      <header className="mb-6 flex items-center justify-between gap-3">
        <p className="font-display text-lg font-medium">Goals</p>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button variant="ghost" size="sm" onClick={signOut}>Sign out</Button>
        </div>
      </header>
      <Card>
        {result ? (
          <>
            <p className="text-sm font-semibold text-accent">Saved for {name}</p>
            <h1 className="mt-2 font-display text-3xl font-medium">Your targets</h1>
            <div className="mt-6">
              <GoalResults result={result} />
            </div>
            <div className="mt-6 flex flex-wrap gap-2">
              <Button onClick={() => navigate("/", { replace: true })}>See today</Button>
              <Button variant="secondary" onClick={() => setResult(null)}>Edit answers</Button>
            </div>
          </>
        ) : (
          <form onSubmit={form.handleSubmit(onSubmit)} noValidate>
            <p className="text-sm font-semibold text-accent">Step {step + 1} of {steps.length}</p>
            <h1 className="mt-2 font-display text-3xl font-medium">{current?.title}</h1>
            <p className="mt-2 text-sm text-muted">Hi {name}. These measurements calculate a calorie target. They are not a medical plan.</p>
            <div className="mt-6">
              {current ? <NutritionFields form={form} part={step === 0 ? "body" : step === 1 ? "activity" : "goal"} /> : null}
            </div>
            <div className="mt-6 flex flex-wrap gap-2">
              {step > 0 ? <Button variant="secondary" onClick={() => setStep(step - 1)}>Back</Button> : null}
              {step < steps.length - 1 ? <Button onClick={() => void next()}>Continue</Button> : (
                <Button type="submit" disabled={pending}>{pending ? "Saving…" : "Save goals"}</Button>
              )}
            </div>
          </form>
        )}
      </Card>
    </main>
  )
}
