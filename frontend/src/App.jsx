import { Navigate, Route, Routes } from 'react-router-dom'
import { getToken } from './api'
import Dashboard from './pages/Dashboard'
import Goal from './pages/Goal'
import Login from './pages/Login'
import Register from './pages/Register'

function Protected({ children }) {
  if (!getToken()) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to={getToken() ? '/app' : '/register'} replace />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route path="/goal" element={<Protected><Goal /></Protected>} />
      <Route path="/app" element={<Protected><Dashboard /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
