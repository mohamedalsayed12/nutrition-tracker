import type { BarcodeResponse, ExerciseSearchResponse, FoodMeasuresResponse, FoodScore, FoodSearchResponse, FrequentFoodsResponse } from "../types/api.ts"
import { request } from "./client.ts"
import { mockFoodScore } from "./mock/score.ts"

export function searchFoods(query: string): Promise<FoodSearchResponse> {
  return request<FoodSearchResponse>("/foods", { query: { q: query } })
}

export function getMeasures(fdcId: number): Promise<FoodMeasuresResponse> {
  return request<FoodMeasuresResponse>(`/foods/${fdcId}/measures`)
}

export function lookupBarcode(code: string): Promise<BarcodeResponse> {
  return request<BarcodeResponse>(`/foods/barcode/${encodeURIComponent(code)}`)
}

export function getFrequentFoods(): Promise<FrequentFoodsResponse> {
  return request<FrequentFoodsResponse>("/foods/frequent")
}

export function searchExercises(query: string): Promise<ExerciseSearchResponse> {
  return request<ExerciseSearchResponse>("/exercises", { query: { q: query }, auth: false })
}

export function getFoodScore(fdcId: number, grams: number): Promise<FoodScore> {
  return mockFoodScore(fdcId, grams)
}
