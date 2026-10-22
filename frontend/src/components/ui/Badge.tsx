import type { HTMLAttributes } from "react"
import { cn } from "../../lib/cn.ts"

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: "accent" | "amber" | "danger" | "neutral"
}

const tones = {
  accent: "bg-accent-soft text-accent",
  amber: "bg-amber/10 text-amber",
  danger: "bg-danger/10 text-danger",
  neutral: "bg-canvas text-muted",
}

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return <span className={cn("inline-flex rounded-full px-2.5 py-1 text-xs font-semibold", tones[tone], className)} {...props} />
}
