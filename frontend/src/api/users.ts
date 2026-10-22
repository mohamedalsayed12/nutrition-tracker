import type { UserProfile } from "../types/api.ts"
import { request } from "./client.ts"

export function getMe(): Promise<UserProfile> {
  return request<UserProfile>("/users/me")
}
