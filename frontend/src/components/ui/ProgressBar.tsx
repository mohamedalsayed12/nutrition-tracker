import { cn } from "../../lib/cn.ts"

type ProgressBarProps = {
  label: string
  value: number
  max?: number
  tone?: "accent" | "amber" | "danger"
  detail?: string
}

const tones = {
  accent: "bg-accent",
  amber: "bg-amber",
  danger: "bg-danger",
}

export function ProgressBar({ label, value, max = 100, tone = "accent", detail }: ProgressBarProps) {
  const percent = max > 0 ? Math.min(Math.max((value / max) * 100, 0), 100) : 0
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between gap-3 text-sm">
        <span className="font-semibold">{label}</span>
        {detail ? <span className="text-muted">{detail}</span> : null}
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-canvas" role="progressbar" aria-valuemin={0} aria-valuemax={max} aria-valuenow={value} aria-label={label}>
        <div className={cn("h-full rounded-full", tones[tone])} style={{ width: `${percent}%` }} />
      </div>
    </div>
  )
}
