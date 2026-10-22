import { useEffect, useState } from "react"
import { storeTheme, storedThemeIsDark, subscribeTheme } from "../lib/theme.ts"

export function ThemeToggle() {
  const [dark, setDark] = useState(storedThemeIsDark)

  useEffect(() => subscribeTheme(() => setDark(storedThemeIsDark())), [])

  return (
    <button
      type="button"
      className="rounded-full border border-line bg-card px-3 py-1.5 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      aria-pressed={dark}
      onClick={() => {
        const next = !dark
        storeTheme(next)
        setDark(next)
      }}
    >
      {dark ? "Light mode" : "Dark mode"}
    </button>
  )
}
