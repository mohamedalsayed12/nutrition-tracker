import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, clearToken, macrosFromNutrients } from '../api'
import CalorieRing from '../components/CalorieRing'
import MacroBars from '../components/MacroBars'
import { formatDateHeading, formatNumber, progressRow } from '../lib/format'

const MEALS = ['breakfast', 'lunch', 'dinner', 'snack']

export default function Today() {
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [logs, setLogs] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const me = await api.me()
      if (me.needs_goal) {
        navigate('/app/goals')
        return
      }
      const [daily, foodLogs] = await Promise.all([api.dailyReport(), api.foodLogs()])
      const now = new Date()
      const items = (foodLogs.items || []).filter((log) => {
        const logged = new Date(log.logged_at)
        return (
          logged.getFullYear() === now.getFullYear()
          && logged.getMonth() === now.getMonth()
          && logged.getDate() === now.getDate()
        )
      })
      setReport(daily)
      setLogs(items)
    } catch (err) {
      setError(err.message)
      if (/unauthorized|token|401/i.test(err.message)) {
        clearToken()
        navigate('/login')
      }
    } finally {
      setLoading(false)
    }
  }, [navigate])

  useEffect(() => { load() }, [load])

  const meals = useMemo(() => {
    const groups = Object.fromEntries(MEALS.map((meal) => [meal, []]))
    for (const log of logs) {
      if (groups[log.meal]) groups[log.meal].push(log)
    }
    return groups
  }, [logs])

  const calories = progressRow(report?.progress, 'Calories')
  const eaten = calories?.logged ?? report?.totals?.Calories ?? 0
  const target = report?.calorie_goal ?? 0
  const exercise = report?.exercise_credit ?? 0
  const left = Math.max(target - eaten, 0)
  const percent = target > 0 ? (eaten / target) * 100 : 0

  return (
    <main className="screen">
      <header className="screen-header">
        <p className="date-line">{formatDateHeading()}</p>
        <h1>Today</h1>
      </header>

      {error && <p className="banner-error">{error}</p>}
      {loading && <p className="muted">Loading today’s plate…</p>}

      {!loading && report && (
        <>
          <section className="card calorie-card">
            <CalorieRing left={left} percent={percent} />
            <ul className="calorie-stats">
              <li><span>Target</span><strong>{formatNumber(target)}</strong></li>
              <li><span>Eaten</span><strong>{formatNumber(eaten)}</strong></li>
              <li><span>Exercise</span><strong>+{formatNumber(exercise)}</strong></li>
            </ul>
          </section>

          <section className="card">
            <MacroBars progress={report.progress} />
          </section>

          <section className="meal-list">
            {MEALS.map((meal) => {
              const items = meals[meal]
              const mealKcal = items.reduce((sum, log) => sum + macrosFromNutrients(log.nutrients).calories, 0)
              return (
                <article key={meal} className="card meal-card">
                  <div className="meal-card__head">
                    <div>
                      <h2>{meal[0].toUpperCase() + meal.slice(1)}</h2>
                      <p>{formatNumber(mealKcal)} kcal</p>
                    </div>
                    <Link to={`/app/add?meal=${meal}`} className="icon-add" aria-label={`Add to ${meal}`}>+</Link>
                  </div>
                  {items.length === 0 ? (
                    <p className="muted empty-meal">Nothing logged yet</p>
                  ) : (
                    <ul className="food-lines">
                      {items.map((log) => (
                        <li key={log.id}>
                          <span>{log.food_name}, {formatNumber(log.grams, 0)} g</span>
                          <strong>{formatNumber(macrosFromNutrients(log.nutrients).calories)} kcal</strong>
                        </li>
                      ))}
                    </ul>
                  )}
                </article>
              )
            })}
          </section>
        </>
      )}
    </main>
  )
}
