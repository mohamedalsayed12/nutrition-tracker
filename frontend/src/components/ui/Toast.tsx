import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react"
import { cn } from "../../lib/cn.ts"

type ToastTone = "info" | "danger"

type ToastAction = {
  label: string
  onClick: () => void
}

type ToastItem = {
  id: number
  message: string
  tone: ToastTone
  action?: ToastAction
}

type ToastContextValue = {
  push: (message: string, tone?: ToastTone, action?: ToastAction) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const push = useCallback((message: string, tone: ToastTone = "info", action?: ToastAction) => {
    const id = Date.now() + Math.floor(Math.random() * 1000)
    setToasts((current) => [...current, { id, message, tone, action }])
    window.setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id))
    }, action ? 6000 : 4000)
  }, [])

  const value = useMemo(() => ({ push }), [push])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4" aria-live="polite">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={cn(
              "pointer-events-auto flex max-w-md items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold shadow-lg",
              toast.tone === "danger" ? "bg-danger text-white" : "bg-ink text-card",
            )}
          >
            <p>{toast.message}</p>
            {toast.action ? (
              <button
                type="button"
                className="rounded-full border border-current px-3 py-1 text-xs focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                onClick={() => {
                  toast.action?.onClick()
                  setToasts((current) => current.filter((item) => item.id !== toast.id))
                }}
              >
                {toast.action.label}
              </button>
            ) : null}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext)
  if (!context) throw new Error("useToast must be used within ToastProvider")
  return context
}
