import { useQuery } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { Navigate, useSearchParams } from "react-router-dom"
import { ApiError } from "../api/client.ts"
import { getFrequentFoods, getMeasures, searchFoods } from "../api/foods.ts"
import { FoodScoreCard } from "../components/food/FoodScoreCard.tsx"
import { Button } from "../components/ui/Button.tsx"
import { Card } from "../components/ui/Card.tsx"
import { Input } from "../components/ui/Input.tsx"
import { Select } from "../components/ui/Select.tsx"
import { Skeleton } from "../components/ui/Skeleton.tsx"
import { Tabs } from "../components/ui/Tabs.tsx"
import { useLogFood } from "../hooks/useLogFood.ts"
import { useNutrition } from "../hooks/useNutrition.ts"
import { mealOptions } from "../lib/meals.ts"
import { gramsFromServing } from "../lib/servings.ts"
import type { FoodMeasure, FoodSummary, Meal } from "../types/api.ts"

export function AddFoodPage() {
  const nutrition = useNutrition()
  const [params] = useSearchParams()
  const requestedMeal = params.get("meal")
  const [meal, setMeal] = useState<Meal>(mealOptions.some((item) => item.id === requestedMeal) ? requestedMeal as Meal : "breakfast")
  const [finder, setFinder] = useState<"search" | "again">("search")
  const [query, setQuery] = useState("")
  const [debounced, setDebounced] = useState("")
  const [selected, setSelected] = useState<FoodSummary | null>(null)
  const logFood = useLogFood()

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(query.trim()), 300)
    return () => window.clearTimeout(timer)
  }, [query])

  const frequent = useQuery({ queryKey: ["foods", "frequent"], queryFn: getFrequentFoods })
  const search = useQuery({
    queryKey: ["foods", "search", debounced],
    queryFn: () => searchFoods(debounced),
    enabled: debounced.length >= 2,
  })

  if (nutrition.isLoading) return <Skeleton className="h-40 w-full" />
  if (nutrition.data && !nutrition.data.configured) return <Navigate to="/onboarding" replace />

  const frequentMeals = frequent.data?.foods[meal] ?? []

  return (
    <div className="space-y-4">
      <h1 className="font-display text-3xl font-medium">Foods</h1>
      <Tabs label="Meal" value={meal} onChange={(value) => setMeal(value as Meal)} tabs={mealOptions.map((item) => ({ id: item.id, label: item.label }))} />
      <Tabs label="How to add a food" value={finder} onChange={(value) => setFinder(value as "search" | "again")} tabs={[{ id: "search", label: "Search" }, { id: "again", label: "Log again" }]} />
      {finder === "search" ? (
        <Card>
          <Input label="Search foods" value={query} onChange={(event) => { setQuery(event.target.value); setSelected(null) }} placeholder="Chicken, banana, or an FDC id" />
          {debounced.length > 0 && debounced.length < 2 ? <p className="mt-3 text-sm text-muted">Type at least 2 characters.</p> : null}
          {search.isLoading ? <Skeleton className="mt-4 h-20 w-full" /> : null}
          {search.isError ? (
            <p className="mt-3 text-sm text-danger">{search.error instanceof ApiError ? search.error.message : "Food search failed."}</p>
          ) : null}
          {search.data && search.data.foods.length === 0 ? <p className="mt-3 text-sm text-muted">No foods matched that search.</p> : null}
          <ul className="mt-3 space-y-2">
            {search.data?.foods.map((food) => (
              <li key={food.fdc_id}>
                <button
                  type="button"
                  className="w-full rounded-2xl border border-line px-3 py-3 text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                  onClick={() => setSelected(food)}
                >
                  <span className="block font-semibold">{food.description}</span>
                  <span className="text-sm text-muted">{food.brand_name ? `${food.brand_name} · ` : ""}{food.data_type} · FDC {food.fdc_id}</span>
                </button>
              </li>
            ))}
          </ul>
        </Card>
      ) : (
        <Card>
          <h2 className="font-display text-xl font-medium">Log again</h2>
          {frequent.isLoading ? <Skeleton className="mt-4 h-16 w-full" /> : null}
          {frequent.isError ? <p className="mt-3 text-sm text-danger">Foods you have logged could not be loaded.</p> : null}
          {!frequent.isLoading && frequentMeals.length === 0 ? (
            <p className="mt-3 text-sm text-muted">Foods you log for this meal will show up here.</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {frequentMeals.map((food) => (
                <li key={`${food.fdc_id}-${food.grams}`} className="flex items-center justify-between gap-3">
                  <span>
                    <span className="block font-semibold">{food.description}</span>
                    <span className="text-sm text-muted">{food.grams} g · logged {food.count} times</span>
                  </span>
                  <Button
                    size="sm"
                    disabled={logFood.isPending}
                    onClick={() => logFood.mutate({ meal, fdc_id: food.fdc_id, grams: food.grams, food_name: food.description })}
                  >
                    Log
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}
      {finder === "search" && selected ? (
        <ServingForm
          key={selected.fdc_id}
          food={selected}
          meal={meal}
          pending={logFood.isPending}
          onLog={(grams) => logFood.mutate({ meal, fdc_id: selected.fdc_id, grams, food_name: selected.description }, { onSuccess: () => setSelected(null) })}
        />
      ) : null}
    </div>
  )
}

function ServingForm({
  food,
  meal,
  pending,
  onLog,
}: {
  food: FoodSummary
  meal: Meal
  pending: boolean
  onLog: (grams: number) => void
}) {
  const measures = useQuery({ queryKey: ["foods", "measures", food.fdc_id], queryFn: () => getMeasures(food.fdc_id) })
  const [measureCode, setMeasureCode] = useState("")
  const [quantity, setQuantity] = useState("1")
  const preferred = measures.data?.measures.find((item) => item.grams === 100) ?? measures.data?.measures[0]
  const chosen = measures.data?.measures.find((item) => item.code === measureCode) ?? preferred
  const parsedQuantity = Number(quantity)
  let grams: number | null = null
  let gramsError = ""
  if (chosen) {
    try {
      grams = gramsFromServing(chosen.grams, parsedQuantity)
    } catch (error) {
      gramsError = error instanceof Error ? error.message : "Enter a valid amount."
    }
  }

  return (
    <Card>
      <h2 className="font-display text-xl font-medium">{food.description}</h2>
      <p className="mt-1 text-sm text-muted">Logging to {meal}.</p>
      {measures.isLoading ? <Skeleton className="mt-4 h-24 w-full" /> : null}
      {measures.isError ? <p className="mt-3 text-sm text-danger">{measures.error instanceof ApiError ? measures.error.message : "Servings could not be loaded."}</p> : null}
      {chosen ? (
        <div className="mt-4 space-y-4">
          <Select
            label="Serving"
            value={chosen.code}
            onChange={(event) => setMeasureCode(event.target.value)}
            options={(measures.data?.measures ?? []).map((item: FoodMeasure) => ({ value: item.code, label: item.label }))}
          />
          <Input label="Quantity" inputMode="decimal" value={quantity} onChange={(event) => setQuantity(event.target.value)} />
          {gramsError ? <p className="text-sm text-danger">{gramsError}</p> : <p className="text-sm font-semibold">{grams} g</p>}
          {grams ? <FoodScoreCard fdcId={food.fdc_id} grams={grams} /> : null}
          <Button disabled={pending || grams == null} onClick={() => { if (grams != null) onLog(grams) }}>{pending ? "Logging…" : "Log food"}</Button>
        </div>
      ) : null}
    </Card>
  )
}
