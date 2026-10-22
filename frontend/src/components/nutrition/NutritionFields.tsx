import type { UseFormReturn } from "react-hook-form"
import { cn } from "../../lib/cn.ts"
import { activityChoices, goalChoices, sexChoices } from "../../lib/nutritionCopy.ts"
import type { NutritionInput } from "../../lib/schemas.ts"
import { Input } from "../ui/Input.tsx"

type NutritionForm = UseFormReturn<NutritionInput>

export function NutritionFields({ form, part }: { form: NutritionForm; part: "body" | "activity" | "goal" | "all" }) {
  const { register, watch, formState } = form
  const errors = formState.errors
  const activity = watch("activity_level")
  const goal = watch("goal")
  const sex = watch("sex")
  const showBody = part === "body" || part === "all"
  const showActivity = part === "activity" || part === "all"
  const showGoal = part === "goal" || part === "all"

  return (
    <div className="space-y-5">
      {showBody ? (
        <>
          <Input label="Age" inputMode="numeric" error={errors.age?.message} {...register("age")} />
          <fieldset>
            <legend className="text-sm font-semibold">Sex</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {sexChoices.map((choice) => (
                <label
                  key={choice.value}
                  className={cn(
                    "cursor-pointer rounded-full border px-4 py-2 text-sm font-semibold",
                    sex === choice.value ? "border-ink bg-ink text-card" : "border-line bg-card text-ink",
                  )}
                >
                  <input type="radio" className="sr-only" value={choice.value} {...register("sex")} />
                  {choice.label}
                </label>
              ))}
            </div>
          </fieldset>
          <Input label="Height (cm)" inputMode="decimal" error={errors.height_cm?.message} {...register("height_cm")} />
          <Input label="Weight (kg)" inputMode="decimal" error={errors.weight_kg?.message} {...register("weight_kg")} />
        </>
      ) : null}
      {showActivity ? (
        <fieldset>
          <legend className="text-sm font-semibold">Usual activity</legend>
          <div className="mt-2 space-y-2">
            {activityChoices.map((choice) => (
              <label
                key={choice.value}
                className={cn(
                  "flex cursor-pointer gap-3 rounded-2xl border p-3",
                  activity === choice.value ? "border-accent bg-accent-soft" : "border-line bg-card",
                )}
              >
                <input type="radio" className="mt-1" value={choice.value} {...register("activity_level")} />
                <span>
                  <span className="block text-sm font-semibold">{choice.label}</span>
                  <span className="mt-1 block text-sm font-normal text-muted">{choice.detail}</span>
                </span>
              </label>
            ))}
          </div>
          {errors.activity_level?.message ? <span className="mt-1 block text-sm text-danger">{errors.activity_level.message}</span> : null}
        </fieldset>
      ) : null}
      {showGoal ? (
        <fieldset>
          <legend className="text-sm font-semibold">Goal</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {goalChoices.map((choice) => (
              <label
                key={choice.value}
                className={cn(
                  "cursor-pointer rounded-full border px-4 py-2 text-sm font-semibold",
                  goal === choice.value ? "border-ink bg-ink text-card" : "border-line bg-card text-ink",
                )}
              >
                <input type="radio" className="sr-only" value={choice.value} {...register("goal")} />
                {choice.label}
              </label>
            ))}
          </div>
          <p className="mt-3 text-sm text-muted">{goalChoices.find((choice) => choice.value === goal)?.detail}</p>
          {part === "all" ? (
            <p className="mt-2 text-sm text-muted">Saving recalculates your targets. The server keeps those numbers, not the goal name, so this choice starts at Maintain each time you open settings.</p>
          ) : null}
        </fieldset>
      ) : null}
    </div>
  )
}
