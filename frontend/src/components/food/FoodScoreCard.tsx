import { useQuery } from "@tanstack/react-query"
import { getFoodScore } from "../../api/foods.ts"
import { Badge } from "../ui/Badge.tsx"
import { Card } from "../ui/Card.tsx"
import { Skeleton } from "../ui/Skeleton.tsx"

export function FoodScoreCard({ fdcId, grams }: { fdcId: number; grams: number }) {
  const score = useQuery({
    queryKey: ["foods", "score", fdcId, grams],
    queryFn: () => getFoodScore(fdcId, grams),
    enabled: grams > 0,
  })

  if (score.isLoading) return <Skeleton className="h-36 w-full" />
  if (score.isError || !score.data) {
    return <p className="text-sm text-muted">The preview score could not be loaded.</p>
  }

  return (
    <Card className="bg-canvas shadow-none">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-muted">Preview score</p>
          <p className="font-display text-4xl font-bold">{score.data.score ?? "—"}</p>
        </div>
        <Badge tone="amber">Mocked</Badge>
      </div>
      <p className="mt-2 text-sm text-muted">
        {score.data.calories_per_100g == null ? "Calories per 100 g are not in this preview." : `${score.data.calories_per_100g} kcal per 100 g in this preview.`}
      </p>
      <ul className="mt-3 space-y-1 text-sm">
        {score.data.reasons.map((reason) => <li key={reason}>{reason}</li>)}
      </ul>
      <ul className="mt-3 space-y-1 text-sm text-muted">
        {score.data.nutrients_per_100kcal.map((nutrient) => (
          <li key={nutrient.name}>
            {nutrient.name}: {nutrient.amount} {nutrient.unit}
            {nutrient.percent_of_target == null ? "" : ` · ${nutrient.percent_of_target}% of target per 100 kcal`}
          </li>
        ))}
      </ul>
    </Card>
  )
}
