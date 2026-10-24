import type { ApiErrorDetail } from "../types/api.ts"
import { clearToken, getToken } from "../lib/auth.ts"

const API_URL = (import.meta.env.VITE_API_URL ?? (import.meta.env.PROD ? "" : "http://localhost:5000")).replace(/\/$/, "")

export class ApiError extends Error {
  readonly status: number
  readonly details: ApiErrorDetail[]

  constructor(status: number, message: string, details: ApiErrorDetail[] = []) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.details = details
  }
}

type Query = Record<string, string | number | boolean | undefined>

type RequestOptions = {
  method?: string
  body?: unknown
  auth?: boolean
  query?: Query
}

export function fieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError)) return {}
  const fields: Record<string, string> = {}
  for (const detail of error.details) {
    const key = [...detail.loc].reverse().find((part) => typeof part === "string" && part !== "body")
    if (typeof key === "string" && fields[key] === undefined) {
      fields[key] = detail.msg.replace(/^Value error,\s*/, "")
    }
  }
  return fields
}

function queryString(query: Query | undefined): string {
  if (!query) return ""
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined) params.set(key, String(value))
  }
  const text = params.toString()
  return text ? `?${text}` : ""
}

function redirectToLogin(): void {
  clearToken()
  if (window.location.pathname !== "/login") {
    window.location.assign("/login")
  }
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers({ Accept: "application/json" })
  if (options.body !== undefined) headers.set("Content-Type", "application/json")
  if (options.auth !== false) {
    const token = getToken()
    if (token) headers.set("Authorization", `Bearer ${token}`)
  }

  let response: Response
  try {
    response = await fetch(`${API_URL}/api/v1${path}${queryString(options.query)}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch {
    throw new ApiError(0, "The API could not be reached. Check that it is running and that FRONTEND_ORIGIN allows this site.")
  }

  if (response.status === 204) return undefined as T
  const text = await response.text()
  let payload: unknown = undefined
  if (text) {
    try {
      payload = JSON.parse(text) as unknown
    } catch {
      throw new ApiError(response.status, "The API returned a response that was not JSON.")
    }
  }

  if (!response.ok) {
    const body = isRecord(payload) ? payload : {}
    const message = typeof body.error === "string"
      ? body.error
      : typeof body.msg === "string"
        ? body.msg
        : "The request could not be completed."
    const details = Array.isArray(body.details) ? body.details.filter(isDetail) : []
    if (response.status === 401 && path !== "/auth/login") redirectToLogin()
    throw new ApiError(response.status, message, details)
  }

  return payload as T
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null
}

function isDetail(value: unknown): value is ApiErrorDetail {
  if (!isRecord(value) || !Array.isArray(value.loc) || typeof value.msg !== "string" || typeof value.type !== "string") {
    return false
  }
  return value.loc.every((part) => typeof part === "string" || typeof part === "number")
}

export function useMocks(): boolean {
  return import.meta.env.VITE_USE_MOCKS === "true"
}
