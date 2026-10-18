import { clampPercent, formatNumber } from '../lib/format'

export default function CalorieRing({ left, percent }) {
  const filled = clampPercent(percent)
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (filled / 100) * circumference

  return (
    <div className="calorie-ring">
      <svg viewBox="0 0 140 140" aria-hidden="true">
        <circle className="calorie-ring__track" cx="70" cy="70" r={radius} />
        <circle
          className="calorie-ring__value"
          cx="70"
          cy="70"
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="calorie-ring__label">
        <strong>{formatNumber(Math.max(left, 0))}</strong>
        <span>kcal left</span>
      </div>
    </div>
  )
}
