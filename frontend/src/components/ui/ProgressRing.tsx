import type { IntakeTone } from "../../lib/progressTone.ts"

type ProgressRingProps = {
  value: number
  max: number
  label: string
  caption?: string
  unit?: string
  tone?: IntakeTone
  size?: "md" | "sm"
}

const strokes = {
  accent: "stroke-accent",
  amber: "stroke-amber",
  danger: "stroke-danger",
}

export function ProgressRing({ value, max, label, caption, unit = "kcal", tone = "accent", size = "md" }: ProgressRingProps) {
  const radius = 46
  const circumference = 2 * Math.PI * radius
  const percent = max > 0 ? Math.min(Math.max(value / max, 0), 1) : 0
  const shown = Math.round(value)
  return (
    <div className={size === "sm" ? "relative grid h-28 w-28 place-items-center" : "relative grid h-40 w-40 place-items-center"}>
      <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90" aria-hidden="true">
        <circle cx="60" cy="60" r={radius} fill="none" className="stroke-canvas" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          className={strokes[tone]}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - percent)}
        />
      </svg>
      <div className="absolute text-center">
        <p className={size === "sm" ? "font-display text-2xl font-bold leading-none" : "font-display text-4xl font-bold leading-none"}>{shown.toLocaleString()}</p>
        <p className="mt-1 text-xs text-muted">{unit}</p>
      </div>
      <p className="sr-only">
        {label}: {shown} of {Math.round(max)} {unit}
        {caption ? `. ${caption}` : ""}
      </p>
    </div>
  )
}
