import { Navigate, Outlet } from 'react-router-dom'
import { getToken } from '../api'
import BottomNav from './BottomNav'

export default function AppShell() {
  if (!getToken()) return <Navigate to="/login" replace />
  return (
    <div className="phone-frame">
      <div className="phone-screen">
        <Outlet />
        <BottomNav />
      </div>
    </div>
  )
}
