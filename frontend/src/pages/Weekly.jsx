import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, clearToken } from '../api'
import MacroBars from '../components/MacroBars'
import { formatNumber } from '../lib/format'

export default function Weekly() {
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      try {
        const data = await api.weeklyReport()
        if (active) setReport(data)
      } catch (err) {
        if (!active) return
        setError(err.message)
        if (/unauthorized|token|401/i.test(err.message)) {
          clearToken()
          navigate('/login')
        }
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [navigate])

  const avgCalories = useMemo(() => {
    const row = (report?.macros || []).find((item) => item.name === 'Calories')
    return row?.average ?? 0
  }, [report])

  const macroProgress = useMemo(() => {
    const targets = {
      Protein: report?.calorie_goal ? (report.calorie_goal * 0.25) / 4 : null,
      Carbohydrates: report?.calorie_goal ? (report.calorie_goal * 0.45) / 4 : null,
      Fat: report?.calorie_goal ? (report.calorie_goal * 0.30) / 9 : null,
    }
    return (report?.macros || [])
      .filter((row) => row.name !== 'Calories')
      .map((row) => ({
        name: row.name,
        average: row.average,
        target: targets[row.name],
      }))
  }, [report])

  const maxBar = Math.max(
    report?.calorie_goal || 0,
    ...((report?.daily_calories || []).map((day) => day.calories) || [0]),
    1,
  )

  return (
    <main className="screen">
      <header className="screen-header">
        <h1>Weekly report</h1>
      </header>

      {error && <p className="banner-error">{error}</p>}
      {loading && <p className="muted">Loading week…</p>}

      {!loading && report && (
        <>
          <section className="card week-stats">
            <div>
              <span>Avg calories</span>
              <strong>{formatNumber(avgCalories)}</strong>
            </div>
            <div>
              <span>Days on target</span>
              <strong>{report.days_on_target}/7</strong>
              <small>within ±10%</small>
            </div>
          </section>

          <section className="card">
            <h2>Calories by day</h2>
            <div className="week-chart" style={{ '--target': `${((report.calorie_goal || 0) / maxBar) * 100}%` }}>
              {(report.daily_calories || []).map((day) => (
                <div key={day.date} className="week-chart__col">
                  <div className="week-chart__bar-wrap">
                    <div
                      className={`week-chart__bar ${day.on_target ? 'is-hit' : ''}`}
                      style={{ height: `${Math.max((day.calories / maxBar) * 100, day.calories ? 6 : 0)}%` }}
                      title={`${day.calories} kcal`}
                    />
                  </div>
                  <span>{day.label}</span>
                </div>
              ))}
              {report.calorie_goal != null && <div className="week-chart__target" />}
            </div>
          </section>

          <section className="card">
            <h2>Average macros</h2>
            <MacroBars progress={macroProgress} averages />
          </section>
        </>
      )}
    </main>
  )
}
