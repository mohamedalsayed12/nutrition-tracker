import type { LoginRequest, LoginResponse, RegisterRequest, UserProfile } from "../types/api.ts"
import { request } from "./client.ts"

export function registerUser(body: RegisterRequest): Promise<UserProfile> {
  return request<UserProfile>("/users", { method: "POST", body, auth: false })
}

export function login(body: LoginRequest): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/login", { method: "POST", body, auth: false })
}
