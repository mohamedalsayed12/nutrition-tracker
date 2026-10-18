import { Navigate, Route, Routes } from 'react-router-dom'
import { getToken } from './api'
import AppShell from './components/AppShell'
import AddFood from './pages/AddFood'
import Goals from './pages/Goals'
import Login from './pages/Login'
import Register from './pages/Register'
import Today from './pages/Today'
import Weekly from './pages/Weekly'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to={getToken() ? '/app' : '/register'} replace />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route path="/app" element={<AppShell />}>
        <Route index element={<Today />} />
        <Route path="add" element={<AddFood />} />
        <Route path="weekly" element={<Weekly />} />
        <Route path="goals" element={<Goals />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
