import type { HTMLAttributes } from "react"
import { cn } from "../../lib/cn.ts"

export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-pulse rounded-2xl bg-line/80", className)} {...props} />
}
