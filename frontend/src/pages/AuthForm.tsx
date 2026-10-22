import { zodResolver } from "@hookform/resolvers/zod"
import { useState, type ReactNode } from "react"
import { useForm } from "react-hook-form"
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom"
import { login, registerUser } from "../api/auth.ts"
import { ApiError, fieldErrors } from "../api/client.ts"
import { getNutrition } from "../api/goals.ts"
import { Button } from "../components/ui/Button.tsx"
import { Card } from "../components/ui/Card.tsx"
import { Input } from "../components/ui/Input.tsx"
import { useToast } from "../components/ui/Toast.tsx"
import { ThemeToggle } from "../components/ThemeToggle.tsx"
import { getToken, setToken } from "../lib/auth.ts"
import { loginSchema, registerSchema, type LoginValues, type RegisterValues } from "../lib/schemas.ts"

export function LoginPage() {
  if (getToken()) return <Navigate to="/" replace />
  return (
    <AuthScreen
      title="Welcome back"
      subtitle="Sign in to see today's meals."
      alternate={{ to: "/register", label: "Create an account" }}
    >
      <LoginForm />
    </AuthScreen>
  )
}

export function RegisterPage() {
  if (getToken()) return <Navigate to="/" replace />
  return (
    <AuthScreen
      title="Create your account"
      subtitle="Then we'll set your daily targets."
      alternate={{ to: "/login", label: "I already have an account" }}
    >
      <RegisterForm />
    </AuthScreen>
  )
}

function LoginForm() {
  const navigate = useNavigate()
  const location = useLocation()
  const toast = useToast()
  const preset = typeof location.state === "object" && location.state && "email" in location.state
    ? String(location.state.email)
    : ""
  const form = useForm<LoginValues>({ resolver: zodResolver(loginSchema), defaultValues: { email: preset, password: "" } })
  const [pending, setPending] = useState(false)

  async function onSubmit(values: LoginValues) {
    setPending(true)
    try {
      const session = await login(values)
      setToken(session.access_token)
      navigate(await nextPath(), { replace: true })
    } catch (error) {
      applyApiErrors(error, (field, message) => {
        if (field === "email" || field === "password") form.setError(field, { message })
      }, toast.push)
    } finally {
      setPending(false)
    }
  }

  return (
    <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)} noValidate>
      <Input label="Email" type="email" autoComplete="email" error={form.formState.errors.email?.message} {...form.register("email")} />
      <Input label="Password" type="password" autoComplete="current-password" error={form.formState.errors.password?.message} {...form.register("password")} />
      <Button type="submit" className="w-full" disabled={pending}>{pending ? "Signing in…" : "Sign in"}</Button>
    </form>
  )
}

function RegisterForm() {
  const navigate = useNavigate()
  const toast = useToast()
  const form = useForm<RegisterValues>({ resolver: zodResolver(registerSchema), defaultValues: { name: "", email: "", password: "" } })
  const [pending, setPending] = useState(false)

  async function onSubmit(values: RegisterValues) {
    setPending(true)
    try {
      await registerUser(values)
      const session = await login({ email: values.email, password: values.password })
      setToken(session.access_token)
      toast.push("Account created.")
      navigate(await nextPath(), { replace: true })
    } catch (error) {
      applyApiErrors(error, (field, message) => {
        if (field === "name" || field === "email" || field === "password") form.setError(field, { message })
      }, toast.push)
      if (error instanceof ApiError && error.status === 409) form.setError("email", { message: error.message })
    } finally {
      setPending(false)
    }
  }

  return (
    <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)} noValidate>
      <Input label="Name" autoComplete="name" error={form.formState.errors.name?.message} {...form.register("name")} />
      <Input label="Email" type="email" autoComplete="email" error={form.formState.errors.email?.message} {...form.register("email")} />
      <Input label="Password" type="password" autoComplete="new-password" hint="At least 8 characters." error={form.formState.errors.password?.message} {...form.register("password")} />
      <Button type="submit" className="w-full" disabled={pending}>{pending ? "Creating account…" : "Create account"}</Button>
    </form>
  )
}

async function nextPath(): Promise<"/onboarding" | "/"> {
  const nutrition = await getNutrition()
  return nutrition.configured ? "/" : "/onboarding"
}

function applyApiErrors(
  error: unknown,
  assign: (field: string, message: string) => void,
  push: (message: string, tone?: "info" | "danger") => void,
) {
  const message = error instanceof ApiError ? error.message : "Something went wrong."
  push(message, "danger")
  for (const [field, fieldMessage] of Object.entries(fieldErrors(error))) assign(field, fieldMessage)
}

function AuthScreen({
  title,
  subtitle,
  alternate,
  children,
}: {
  title: string
  subtitle: string
  alternate: { to: string; label: string }
  children: ReactNode
}) {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <p className="font-display text-lg font-medium">Nutrition tracker</p>
        <ThemeToggle />
      </div>
      <Card>
        <h1 className="font-display text-3xl font-medium">{title}</h1>
        <p className="mt-2 text-sm text-muted">{subtitle}</p>
        <div className="mt-6">{children}</div>
      </Card>
      <p className="mt-4 text-center text-sm">
        <Link className="font-semibold text-accent underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent" to={alternate.to}>
          {alternate.label}
        </Link>
      </p>
    </main>
  )
}
