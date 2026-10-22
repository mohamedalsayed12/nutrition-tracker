import type { ActivityLog, ActivityLogRequest, Page } from "../types/api.ts"
import { request } from "./client.ts"

export function listActivityLogs(page = 1, perPage = 20): Promise<Page<ActivityLog>> {
  return request<Page<ActivityLog>>("/activity-logs", { query: { page, per_page: perPage } })
}

export function createActivityLog(body: ActivityLogRequest): Promise<ActivityLog> {
  return request<ActivityLog>("/activity-logs", { method: "POST", body })
}

export function getActivityLog(id: number): Promise<ActivityLog> {
  return request<ActivityLog>(`/activity-logs/${id}`)
}

export function updateActivityLog(id: number, body: ActivityLogRequest): Promise<ActivityLog> {
  return request<ActivityLog>(`/activity-logs/${id}`, { method: "PUT", body })
}

export function deleteActivityLog(id: number): Promise<void> {
  return request<void>(`/activity-logs/${id}`, { method: "DELETE" })
}

export async function listRecentActivityLogs(): Promise<ActivityLog[]> {
  const first = await listActivityLogs(1, 100)
  const items = [...first.items]
  const pages = Math.min(Math.ceil(first.total / first.per_page), 5)
  for (let page = 2; page <= pages; page += 1) {
    const next = await listActivityLogs(page, 100)
    items.push(...next.items)
  }
  return items
}
