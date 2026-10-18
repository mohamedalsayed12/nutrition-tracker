const ORDER = ['Calories', 'Protein', 'Carbohydrates', 'Fat']

function fillPercent(row) {
  if (row?.percent == null || Number.isNaN(row.percent)) return 0
  return Math.max(0, Math.min(row.percent, 100))
}

export default function MacroBar({ progress, loading }) {
  const byName = Object.fromEntries((progress || []).map((row) => [row.name, row]))
  const rows = ORDER.map((name) => byName[name]).filter(Boolean)

  return (
    <header className="macro-bar" aria-label="Daily macro progress">
      <div className="macro-bar__brand">
        <span className="macro-bar__mark">Harvest</span>
        <span className="macro-bar__hint">{loading ? 'Updating…' : 'Today’s targets'}</span>
      </div>
      <div className="macro-bar__tracks">
        {rows.length === 0 && !loading && (
          <p className="macro-bar__empty">Choose a goal to unlock your macro bar.</p>
        )}
        {rows.map((row) => {
          const filled = fillPercent(row)
          return (
            <div key={row.name} className="macro-track">
              <div className="macro-track__meta">
                <span>{row.name}</span>
                <span>
                  {row.logged == null ? '—' : row.logged}
                  <small> / {row.target_label}</small>
                </span>
              </div>
              <div className="macro-track__rail" role="progressbar" aria-valuenow={filled} aria-valuemin={0} aria-valuemax={100} aria-label={row.name}>
                <div
                  className={`macro-track__fill macro-track__fill--${row.name.toLowerCase()}`}
                  style={{ width: `${filled}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </header>
  )
}
