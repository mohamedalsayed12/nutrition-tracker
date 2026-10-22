import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ApiError } from "../api/client.ts"
import { createFoodLog, deleteFoodLog } from "../api/foodLogs.ts"
import { useToast } from "../components/ui/Toast.tsx"
import type { FoodLog, FoodLogRequest } from "../types/api.ts"

type LogInput = FoodLogRequest & { food_name: string }

export function useLogFood() {
  const queryClient = useQueryClient()
  const toast = useToast()

  return useMutation({
    mutationFn: (input: LogInput) => createFoodLog(
      input.barcode ? { meal: input.meal, barcode: input.barcode, grams: input.grams }
        : { meal: input.meal, fdc_id: input.fdc_id, grams: input.grams },
    ),
    onMutate: async (input) => {
      await queryClient.cancelQueries({ queryKey: ["food-logs"] })
      const previous = queryClient.getQueryData<FoodLog[]>(["food-logs", "recent"])
      const temp: FoodLog = {
        id: -Date.now(),
        meal: input.meal,
        fdc_id: input.fdc_id ?? null,
        barcode: input.barcode ?? null,
        food_name: input.food_name,
        grams: input.grams,
        nutrients: [],
        logged_at: new Date().toISOString(),
      }
      queryClient.setQueryData<FoodLog[]>(["food-logs", "recent"], (current) => [temp, ...(current ?? [])])
      return { previous, tempId: temp.id }
    },
    onError: (error, _input, context) => {
      if (context) queryClient.setQueryData(["food-logs", "recent"], context.previous)
      toast.push(error instanceof ApiError ? error.message : "The food could not be logged.", "danger")
    },
    onSuccess: async (saved, input, context) => {
      queryClient.setQueryData<FoodLog[]>(["food-logs", "recent"], (current) => (
        (current ?? []).map((item) => item.id === context?.tempId ? saved : item)
      ))
      await queryClient.invalidateQueries({ queryKey: ["reports"] })
      await queryClient.invalidateQueries({ queryKey: ["foods", "frequent"] })
      toast.push(`${input.food_name} logged.`, "info", {
        label: "Undo",
        onClick: () => {
          void deleteFoodLog(saved.id).then(async () => {
            await queryClient.invalidateQueries({ queryKey: ["food-logs"] })
            await queryClient.invalidateQueries({ queryKey: ["reports"] })
            await queryClient.invalidateQueries({ queryKey: ["foods", "frequent"] })
            toast.push("Log removed.")
          }).catch((error: unknown) => {
            toast.push(error instanceof ApiError ? error.message : "The log could not be removed.", "danger")
          })
        },
      })
    },
  })
}
