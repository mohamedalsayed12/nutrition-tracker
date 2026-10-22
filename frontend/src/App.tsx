import { Navigate, Route, Routes } from "react-router-dom"
import { AppShell } from "./components/AppShell.tsx"
import { RequireAuth } from "./components/RequireAuth.tsx"
import { AddFoodPage } from "./pages/AddFood.tsx"
import { LoginPage, RegisterPage } from "./pages/AuthForm.tsx"
import { OnboardingPage } from "./pages/Onboarding.tsx"
import { SettingsPage } from "./pages/Settings.tsx"
import { TodayPage } from "./pages/Today.tsx"
import { WeeklyPage } from "./pages/Weekly.tsx"

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<RequireAuth />}>
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route element={<AppShell />}>
          <Route path="/" element={<TodayPage />} />
          <Route path="/add" element={<AddFoodPage />} />
          <Route path="/weekly" element={<WeeklyPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
