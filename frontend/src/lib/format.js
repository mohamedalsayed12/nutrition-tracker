export function formatDateHeading(date = new Date()) {
  return date.toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
  })
}

export function formatNumber(value, digits = 0) {
  if (value == null || Number.isNaN(Number(value))) return '—'
  return Number(value).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })
}

export function clampPercent(value) {
  if (value == null || Number.isNaN(Number(value))) return 0
  return Math.max(0, Math.min(100, Number(value)))
}

export function progressRow(progress, name) {
  return (progress || []).find((row) => row.name === name) || null
}
