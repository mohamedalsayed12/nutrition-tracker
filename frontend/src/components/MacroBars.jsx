import { clampPercent, formatNumber } from '../lib/format'

const MACROS = [
  { key: 'Protein', className: 'protein', unit: 'g' },
  { key: 'Carbohydrates', label: 'Carbs', className: 'carbs', unit: 'g' },
  { key: 'Fat', className: 'fat', unit: 'g' },
]

function parseTargetGrams(row) {
  if (row?.target != null) return Number(row.target)
  const match = String(row?.target_label || '').match(/([\d.]+)\s*g\s*$/i)
  if (match) return Number(match[1])
  const range = String(row?.target_label || '').match(/([\d.]+)\s*-\s*([\d.]+)/)
  if (range) return Number(range[2])
  return null
}

export default function MacroBars({ progress, averages = false }) {
  return (
    <div className="macro-bars">
      {MACROS.map((macro) => {
        const row = (progress || []).find((item) => item.name === macro.key)
        const logged = averages ? row?.average : row?.logged
        const target = averages ? row?.target : parseTargetGrams(row)
        const percent = averages
          ? (logged != null && target ? (logged / target) * 100 : 0)
          : row?.percent
        return (
          <div key={macro.key} className="macro-row">
            <div className="macro-row__meta">
              <span>{macro.label || macro.key}</span>
              <span>
                {logged == null ? '—' : formatNumber(logged, 0)}
                {' / '}
                {target == null ? '—' : formatNumber(target, 0)}
                {' g'}
              </span>
            </div>
            <div className="macro-row__rail">
              <div
                className={`macro-row__fill macro-row__fill--${macro.className}`}
                style={{ width: `${clampPercent(percent)}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
