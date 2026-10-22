const THEME_KEY = "nutrition.theme"
const THEME_EVENT = "nutrition-theme"

export function applyStoredTheme(): void {
  document.documentElement.classList.toggle("dark", localStorage.getItem(THEME_KEY) === "dark")
}

export function storedThemeIsDark(): boolean {
  return document.documentElement.classList.contains("dark")
}

export function storeTheme(dark: boolean): void {
  document.documentElement.classList.toggle("dark", dark)
  localStorage.setItem(THEME_KEY, dark ? "dark" : "light")
  window.dispatchEvent(new Event(THEME_EVENT))
}

export function subscribeTheme(listener: () => void): () => void {
  window.addEventListener(THEME_EVENT, listener)
  return () => window.removeEventListener(THEME_EVENT, listener)
}
