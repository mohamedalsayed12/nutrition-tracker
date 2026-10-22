import type { HealthSettings, HealthSettingsRequest, MacroSplit, MacroSplitRequest } from "../types/api.ts"
import { request } from "./client.ts"

export function getMacroSplit(): Promise<MacroSplit> {
  return request<MacroSplit>("/settings/macro-split")
}

export function saveMacroSplit(body: MacroSplitRequest): Promise<MacroSplitRequest> {
  return request<MacroSplitRequest>("/settings/macro-split", { method: "PUT", body })
}

export function resetMacroSplit(): Promise<void> {
  return request<void>("/settings/macro-split", { method: "DELETE" })
}

export function getHealthSettings(): Promise<HealthSettings> {
  return request<HealthSettings>("/settings/health")
}

export function saveHealthSettings(body: HealthSettingsRequest): Promise<HealthSettings> {
  return request<HealthSettings>("/settings/health", { method: "PUT", body })
}
