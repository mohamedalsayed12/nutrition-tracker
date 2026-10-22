import { Navigate, Outlet } from "react-router-dom"
import { getToken } from "../lib/auth.ts"

export function RequireAuth() {
  if (!getToken()) return <Navigate to="/login" replace />
  return <Outlet />
}
