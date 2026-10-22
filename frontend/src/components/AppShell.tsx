import { NavLink, Outlet } from "react-router-dom"
import { cn } from "../lib/cn.ts"
import { ThemeToggle } from "./ThemeToggle.tsx"

const links = [
  { to: "/", label: "Diary", end: true },
  { to: "/weekly", label: "Trends", end: false },
  { to: "/add", label: "Foods", end: false },
  { to: "/settings", label: "Settings", end: false },
]

export function AppShell() {
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="hidden border-r border-line bg-card lg:flex lg:flex-col lg:px-4 lg:py-6">
        <p className="px-3 font-display text-lg font-medium">Nutrition tracker</p>
        <nav className="mt-8 flex flex-col gap-1" aria-label="Primary">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => cn(
                "rounded-2xl px-3 py-2.5 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
                isActive ? "bg-accent-soft text-accent" : "text-muted hover:bg-canvas",
              )}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="pb-24 lg:pb-0">
        <header className="flex items-center justify-between px-4 py-4 lg:px-8">
          <p className="font-display text-lg font-medium lg:hidden">Nutrition tracker</p>
          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </header>
        <main className="mx-auto w-full max-w-5xl px-4 pb-8 lg:px-8">
          <Outlet />
        </main>
      </div>
      <nav className="fixed inset-x-0 bottom-0 grid grid-cols-4 border-t border-line bg-card px-2 py-2 lg:hidden" aria-label="Primary">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) => cn(
              "rounded-2xl py-2 text-center text-xs font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
              isActive ? "text-accent" : "text-muted",
            )}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
