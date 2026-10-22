import { forwardRef, useId, type SelectHTMLAttributes } from "react"
import { cn } from "../../lib/cn.ts"

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label: string
  error?: string
  options: Array<{ value: string; label: string }>
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, error, options, id, className, ...props },
  ref,
) {
  const generatedId = useId()
  const selectId = id ?? generatedId
  return (
    <label className="block text-sm font-semibold" htmlFor={selectId}>
      {label}
      <select
        ref={ref}
        id={selectId}
        aria-invalid={error ? true : undefined}
        className={cn(
          "mt-1.5 w-full rounded-xl border bg-card px-3 py-2.5 font-normal text-ink outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
          error ? "border-danger" : "border-line",
          className,
        )}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error ? <span className="mt-1 block font-normal text-danger">{error}</span> : null}
    </label>
  )
})
