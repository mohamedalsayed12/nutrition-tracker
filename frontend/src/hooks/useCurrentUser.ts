import { useQuery } from "@tanstack/react-query"
import { getMe } from "../api/users.ts"

export function useCurrentUser() {
  return useQuery({ queryKey: ["users", "me"], queryFn: getMe })
}
