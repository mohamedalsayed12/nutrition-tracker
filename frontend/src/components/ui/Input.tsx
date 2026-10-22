import { forwardRef, useId, type InputHTMLAttributes } from "react"
import { cn } from "../../lib/cn.ts"

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  error?: string
  hint?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, hint, id, className, ...props },
  ref,
) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  const messageId = `${inputId}-message`
  return (
    <label className="block text-sm font-semibold" htmlFor={inputId}>
      {label}
      <input
        ref={ref}
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error || hint ? messageId : undefined}
        className={cn(
          "mt-1.5 w-full rounded-xl border bg-card px-3 py-2.5 font-normal text-ink outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
          error ? "border-danger" : "border-line",
          className,
        )}
        {...props}
      />
      {error || hint ? (
        <span id={messageId} className={cn("mt-1 block font-normal", error ? "text-danger" : "text-muted")}>
          {error || hint}
        </span>
      ) : null}
    </label>
  )
})
