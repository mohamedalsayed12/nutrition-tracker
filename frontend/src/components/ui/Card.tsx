import type { HTMLAttributes } from "react"
import { cn } from "../../lib/cn.ts"

export function Card({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return <section className={cn("rounded-3xl border border-line bg-card p-5 shadow-sm", className)} {...props} />
}
