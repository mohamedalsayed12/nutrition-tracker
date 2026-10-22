import type { ApiToken, NewApiToken } from "../types/api.ts"
import { request } from "./client.ts"

export function listApiTokens(): Promise<{ tokens: ApiToken[] }> {
  return request<{ tokens: ApiToken[] }>("/api-tokens")
}

export function createApiToken(name: string, timezone: string): Promise<NewApiToken> {
  return request<NewApiToken>("/api-tokens", { method: "POST", body: { name, timezone } })
}

export function deleteApiToken(id: number): Promise<void> {
  return request<void>(`/api-tokens/${id}`, { method: "DELETE" })
}
