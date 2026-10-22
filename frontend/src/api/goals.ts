import type {
  CalorieGoalRequest,
  CalorieGoalResponse,
  NutritionGoals,
  NutritionSetupRequest,
  NutritionSetupResponse,
} from "../types/api.ts"
import { request } from "./client.ts"

export function getNutrition(): Promise<NutritionGoals> {
  return request<NutritionGoals>("/goals/nutrition")
}

export function saveNutrition(body: NutritionSetupRequest): Promise<NutritionSetupResponse> {
  return request<NutritionSetupResponse>("/goals/nutrition", { method: "PUT", body })
}

export function getCalories(): Promise<CalorieGoalResponse> {
  return request<CalorieGoalResponse>("/goals/calories")
}

export function saveCalories(body: CalorieGoalRequest): Promise<CalorieGoalResponse> {
  return request<CalorieGoalResponse>("/goals/calories", { method: "PUT", body })
}
