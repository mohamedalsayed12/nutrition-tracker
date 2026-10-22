import type { FoodLog, FoodLogRequest, Page } from "../types/api.ts"
import { request } from "./client.ts"

export function listFoodLogs(page = 1, perPage = 20): Promise<Page<FoodLog>> {
  return request<Page<FoodLog>>("/food-logs", { query: { page, per_page: perPage } })
}

export function createFoodLog(body: FoodLogRequest): Promise<FoodLog> {
  return request<FoodLog>("/food-logs", { method: "POST", body })
}

export function getFoodLog(id: number): Promise<FoodLog> {
  return request<FoodLog>(`/food-logs/${id}`)
}

export function updateFoodLog(id: number, body: FoodLogRequest): Promise<FoodLog> {
  return request<FoodLog>(`/food-logs/${id}`, { method: "PUT", body })
}

export function deleteFoodLog(id: number): Promise<void> {
  return request<void>(`/food-logs/${id}`, { method: "DELETE" })
}

export async function listRecentFoodLogs(): Promise<FoodLog[]> {
  return listRecent(listFoodLogs)
}

async function listRecent<T>(load: (page: number, perPage: number) => Promise<Page<T>>): Promise<T[]> {
  const first = await load(1, 100)
  const items = [...first.items]
  const pages = Math.min(Math.ceil(first.total / first.per_page), 5)
  for (let page = 2; page <= pages; page += 1) {
    const next = await load(page, 100)
    items.push(...next.items)
  }
  return items
}
