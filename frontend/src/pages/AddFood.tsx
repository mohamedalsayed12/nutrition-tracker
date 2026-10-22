import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query"
import { lazy, Suspense, useEffect, useRef, useState } from "react"
import { Navigate, useSearchParams } from "react-router-dom"
import { ApiError } from "../api/client.ts"
import { getFrequentFoods, getMeasures, lookupBarcode, searchFoods } from "../api/foods.ts"
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

// The camera code is only downloaded when someone taps "Scan barcode".
const BarcodeScanner = lazy(() => import("../components/food/BarcodeScanner.tsx"))

function prefetchMeasures(queryClient: ReturnType<typeof useQueryClient>, fdcId: number) {
  return queryClient.prefetchQuery({
    queryKey: ["foods", "measures", fdcId],
    queryFn: () => getMeasures(fdcId),
    staleTime: 30 * 60 * 1000,
  })
}

/** A food picked from search, or found by barcode (which arrives with its servings). */
type Selected = FoodSummary & { measures?: FoodMeasure[]; source?: string }

export function AddFoodPage() {
  const nutrition = useNutrition()
  const [params] = useSearchParams()
  const requestedMeal = params.get("meal")
  const [meal, setMeal] = useState<Meal>(mealOptions.some((item) => item.id === requestedMeal) ? requestedMeal as Meal : "breakfast")
  const [finder, setFinder] = useState<"search" | "again">("search")
  const [query, setQuery] = useState("")
  const [debounced, setDebounced] = useState("")
  const [selected, setSelected] = useState<Selected | null>(null)
  const [scanning, setScanning] = useState(false)
  const [scanError, setScanError] = useState("")
  const [lookingUp, setLookingUp] = useState(false)
  const logFood = useLogFood()

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(query.trim()), 200)
    return () => window.clearTimeout(timer)
  }, [query])

  const frequent = useQuery({ queryKey: ["foods", "frequent"], queryFn: getFrequentFoods })
  const queryClient = useQueryClient()
  const search = useQuery({
    queryKey: ["foods", "search", debounced.toLowerCase()],
    queryFn: () => searchFoods(debounced),
    enabled: debounced.length >= 2,
    // Keep the last results on screen while the next search loads, and reuse
    // results for 30 minutes (USDA data doesn't change during a session).
    placeholderData: keepPreviousData,
    staleTime: 30 * 60 * 1000,
  })

  // Load serving sizes for the top results in the background, so tapping one
  // opens the quantity panel straight away.
  useEffect(() => {
    for (const food of search.data?.foods.slice(0, 5) ?? []) {
      if (food.fdc_id != null) void prefetchMeasures(queryClient, food.fdc_id)
    }
  }, [search.data, queryClient])

  if (nutrition.isLoading) return <Skeleton className="h-40 w-full" />
  if (nutrition.data && !nutrition.data.configured) return <Navigate to="/onboarding" replace />

  const frequentMeals = frequent.data?.foods[meal] ?? []

  async function onBarcode(code: string) {
    setScanning(false)
    setScanError("")
    setLookingUp(true)
    try {
      const found = await lookupBarcode(code)
      setFinder("search")
      setSelected({ ...found.food, measures: found.measures })
    } catch (error) {
      setScanError(error instanceof ApiError ? error.message : "That barcode could not be looked up.")
    } finally {
      setLookingUp(false)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="font-display text-3xl font-medium">Foods</h1>
      <Tabs label="Meal" value={meal} onChange={(value) => setMeal(value as Meal)} tabs={mealOptions.map((item) => ({ id: item.id, label: item.label }))} />
      <Tabs label="How to add a food" value={finder} onChange={(value) => setFinder(value as "search" | "again")} tabs={[{ id: "search", label: "Search" }, { id: "again", label: "Log again" }]} />
      {finder === "search" ? (
        <Card>
          <div className="flex items-end gap-2">
            <div className="min-w-0 flex-1">
              <Input label="Search foods" value={query} onChange={(event) => { setQuery(event.target.value); setSelected(null) }} placeholder="Food or barcode" />
            </div>
            <Button variant="secondary" className="shrink-0" aria-label="Scan a barcode" onClick={() => { setScanError(""); setScanning(true) }}>
              <BarcodeIcon /> <span className="ml-1.5">Scan</span>
            </Button>
          </div>
          {lookingUp ? <p className="mt-3 text-sm text-muted">Looking up barcode…</p> : null}
          {scanError ? <p className="mt-3 text-sm text-danger" role="alert">{scanError}</p> : null}
          {debounced.length > 0 && debounced.length < 2 ? <p className="mt-3 text-sm text-muted">Type at least 2 characters.</p> : null}
          {/^\d{8,14}$/.test(debounced) ? (
            <Button variant="secondary" size="sm" className="mt-3" onClick={() => void onBarcode(debounced)}>
              Look up barcode {debounced}
            </Button>
          ) : null}
          {search.isLoading ? <Skeleton className="mt-4 h-20 w-full" /> : null}
          {search.isFetching && !search.isLoading ? <p className="mt-2 text-xs text-muted" aria-live="polite">Searching…</p> : null}
          {search.isError ? (
            <p className="mt-3 text-sm text-danger">{search.error instanceof ApiError ? search.error.message : "Food search failed."}</p>
          ) : null}
          {search.data && search.data.foods.length === 0 ? <p className="mt-3 text-sm text-muted">No foods matched that search.</p> : null}
          <ul className="mt-3 space-y-2">
            {search.data?.foods.map((food) => (
              <li key={food.fdc_id ?? food.barcode ?? food.description}>
                <button
                  type="button"
                  className="w-full rounded-2xl border border-line px-3 py-3 text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                  onPointerDown={() => { if (food.fdc_id != null) void prefetchMeasures(queryClient, food.fdc_id) }}
                  onClick={() => setSelected(food)}
                >
                  <span className="block font-semibold">{food.description}</span>
                  <span className="text-sm text-muted">
                    {food.previously_logged ? <span className="font-semibold text-accent">Logged before · </span> : null}
                    {food.brand_name ? `${food.brand_name} · ` : ""}{food.data_type === "Branded" ? "Branded" : "USDA"}
                  </span>
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
                <li key={`${food.fdc_id ?? food.barcode}-${food.grams}`} className="flex items-center justify-between gap-3">
                  <span>
                    <span className="block font-semibold">{food.description}</span>
                    <span className="text-sm text-muted">{food.grams} g · logged {food.count} times</span>
                  </span>
                  <Button
                    size="sm"
                    disabled={logFood.isPending}
                    onClick={() => logFood.mutate({ meal, fdc_id: food.fdc_id, barcode: food.barcode, grams: food.grams, food_name: food.description })}
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
        <ServingSheet
          key={selected.fdc_id ?? selected.barcode ?? selected.description}
          food={selected}
          meal={meal}
          pending={logFood.isPending}
          onClose={() => setSelected(null)}
          onLog={(grams) => logFood.mutate(
            { meal, fdc_id: selected.fdc_id, barcode: selected.fdc_id == null ? selected.barcode : null, grams, food_name: selected.description },
            { onSuccess: () => setSelected(null) },
          )}
        />
      ) : null}
      {scanning ? (
        <Suspense fallback={null}>
          <BarcodeScanner onDetected={(code) => void onBarcode(code)} onClose={() => setScanning(false)} />
        </Suspense>
      ) : null}
    </div>
  )
}

// Opens over the search results as soon as a food is tapped: a sheet from the
// bottom on phones, a centred panel on larger screens. Quantity and serving sit
// on one row with the Log button under them, so nothing needs scrolling.
function ServingSheet({
  food,
  meal,
  pending,
  onClose,
  onLog,
}: {
  food: Selected
  meal: Meal
  pending: boolean
  onClose: () => void
  onLog: (grams: number) => void
}) {
  const fetched = useQuery({
    queryKey: ["foods", "measures", food.fdc_id],
    queryFn: () => getMeasures(food.fdc_id as number),
    enabled: food.measures == null && food.fdc_id != null,
    staleTime: 30 * 60 * 1000,
  })
  const measures = food.measures ? { data: { measures: food.measures }, isLoading: false, isError: false, error: null } : fetched
  const [measureCode, setMeasureCode] = useState("")
  const [quantity, setQuantity] = useState("1")
  const panel = useRef<HTMLDivElement>(null)
  const preferred = measures.data?.measures.find((item) => item.default) ?? measures.data?.measures[0]
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
  const mealLabel = mealOptions.find((item) => item.id === meal)?.label ?? meal

  const closeRef = useRef(onClose)
  useEffect(() => { closeRef.current = onClose })
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") closeRef.current() }
    document.addEventListener("keydown", onKey)
    const overflow = document.body.style.overflow
    document.body.style.overflow = "hidden"
    panel.current?.focus()
    return () => {
      document.removeEventListener("keydown", onKey)
      document.body.style.overflow = overflow
    }
  }, [])

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      <button type="button" aria-label="Close" className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="serving-title"
        tabIndex={-1}
        className="relative w-full max-w-lg rounded-t-3xl border border-line bg-card px-5 pt-3 pb-[max(1.25rem,env(safe-area-inset-bottom))] shadow-xl outline-none sm:rounded-3xl sm:pb-5"
      >
        <div className="mx-auto mb-3 h-1.5 w-10 rounded-full bg-line sm:hidden" aria-hidden="true" />
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 id="serving-title" className="font-display text-xl font-medium">{food.description}</h2>
            <p className="mt-0.5 text-sm text-muted">
              {food.brand_name ? `${food.brand_name} · ` : ""}{food.source ? `${food.source} · ` : ""}Add to {mealLabel}
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>Cancel</Button>
        </div>
        {measures.isLoading ? <Skeleton className="mt-4 h-24 w-full" /> : null}
        {measures.isError ? <p className="mt-3 text-sm text-danger">{measures.error instanceof ApiError ? measures.error.message : "Servings could not be loaded."}</p> : null}
        {chosen ? (
          <form
            className="mt-4 space-y-4"
            onSubmit={(event) => { event.preventDefault(); if (grams != null) onLog(grams) }}
          >
            <div className="grid grid-cols-[6rem_1fr] gap-3">
              <Input
                label="Quantity"
                inputMode="decimal"
                value={quantity}
                onFocus={(event) => event.currentTarget.select()}
                onChange={(event) => setQuantity(event.target.value)}
              />
              <Select
                label="Serving"
                value={chosen.code}
                onChange={(event) => setMeasureCode(event.target.value)}
                options={(measures.data?.measures ?? []).map((item: FoodMeasure) => ({ value: item.code, label: item.label }))}
              />
            </div>
            {gramsError ? <p className="text-sm text-danger">{gramsError}</p> : <p className="text-sm text-muted">{grams} g</p>}
            <Button type="submit" className="w-full" disabled={pending || grams == null}>{pending ? "Adding…" : `Add to ${mealLabel}`}</Button>
          </form>
        ) : null}
      </div>
    </div>
  )
}

function BarcodeIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true" className="h-5 w-5">
      <path d="M3 5v10M6 5v10M8.5 5v10M12 5v10M14 5v10M17 5v10" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}
