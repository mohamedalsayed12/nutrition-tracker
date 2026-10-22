import { useQuery } from "@tanstack/react-query"
import { getNutrition } from "../api/goals.ts"

export function useNutrition() {
  return useQuery({ queryKey: ["goals", "nutrition"], queryFn: getNutrition })
}
