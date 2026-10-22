import type { ButtonHTMLAttributes } from "react"
import { cn } from "../../lib/cn.ts"

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger"
  size?: "md" | "sm"
}

const variants = {
  primary: "bg-accent text-white hover:brightness-110",
  secondary: "border border-line bg-card text-ink hover:bg-accent-soft",
  ghost: "text-ink hover:bg-accent-soft",
  danger: "bg-danger text-white hover:brightness-110",
}

const sizes = {
  md: "min-h-11 px-4 text-base",
  sm: "min-h-9 px-3 text-sm",
}

export function Button({ variant = "primary", size = "md", className, type = "button", ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center rounded-full font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  )
}
