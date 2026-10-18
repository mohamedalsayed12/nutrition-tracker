import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, clearToken, macrosFromNutrients } from '../api'
import CalorieRing from '../components/CalorieRing'
import MacroBars from '../components/MacroBars'
import { formatDateHeading, formatNumber, progressRow } from '../lib/format'

const MEALS = ['breakfast', 'lunch', 'dinner']

function todayIso() {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function isSameDay(value, now = new Date()) {
  const logged = new Date(value)
  return (
    logged.getFullYear() === now.getFullYear()
    && logged.getMonth() === now.getMonth()
    && logged.getDate() === now.getDate()
  )
}

export default function Today() {
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [logs, setLogs] = useState([])
  const [activities, setActivities] = useState([])
  const [sex, setSex] = useState(null)
  const [healthConditions, setHealthConditions] = useState([])
  const [periodToday, setPeriodToday] = useState(false)
  const [periodBusy, setPeriodBusy] = useState(false)
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
      const day = todayIso()
      const [daily, foodLogs, activityLogs, health, dayConditions, nutrition] = await Promise.all([
        api.dailyReport(),
        api.foodLogs(),
        api.activityLogs(),
        api.getHealth().catch(() => ({ conditions: [] })),
        api.getDayConditions(day).catch(() => ({ conditions: [] })),
        api.getNutrition().catch(() => null),
      ])
      setSex(nutrition?.sex || me.profile?.sex || null)
      setHealthConditions(health.conditions || [])
      setPeriodToday((dayConditions.conditions || []).includes('menstruation'))
      setReport(daily)
      setLogs((foodLogs.items || []).filter((log) => isSameDay(log.logged_at)))
      setActivities((activityLogs.items || []).filter((log) => isSameDay(log.logged_at)))
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
  const exerciseKcal = activities.reduce((sum, item) => sum + (Number(item.calories_burned) || 0), 0)
  const canLogPeriod = sex === 'female' && !healthConditions.includes('pregnancy')

  async function togglePeriod() {
    if (!canLogPeriod || periodBusy) return
    setPeriodBusy(true)
    setError('')
    const day = todayIso()
    const next = !periodToday
    try {
      if (next) {
        await api.setDayConditions(day, { conditions: ['menstruation'] })
      } else {
        await api.clearDayConditions(day)
      }
      setPeriodToday(next)
      const daily = await api.dailyReport()
      setReport(daily)
    } catch (err) {
      setError(err.message)
    } finally {
      setPeriodBusy(false)
    }
  }

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

          {canLogPeriod && (
            <section className="card period-card">
              <div className="period-card__row">
                <div>
                  <h2>Period today</h2>
                  <p className="muted">Raises iron (+5 mg) and vitamin C (+35 mg) for today</p>
                </div>
                <button
                  type="button"
                  className={`toggle-btn ${periodToday ? 'is-on' : ''}`}
                  aria-pressed={periodToday}
                  disabled={periodBusy}
                  onClick={togglePeriod}
                >
                  {periodToday ? 'On' : 'Off'}
                </button>
              </div>
            </section>
          )}

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

            <article className="card meal-card">
              <div className="meal-card__head">
                <div>
                  <h2>Exercise</h2>
                  <p>{formatNumber(exerciseKcal)} kcal burned</p>
                </div>
                <Link to="/app/exercise" className="icon-add" aria-label="Add exercise">+</Link>
              </div>
              {activities.length === 0 ? (
                <p className="muted empty-meal">No exercise logged yet</p>
              ) : (
                <ul className="food-lines">
                  {activities.map((item) => (
                    <li key={item.id}>
                      <span>
                        {item.activity}
                        {item.duration_minutes != null && ` · ${formatNumber(item.duration_minutes, 0)} min`}
                      </span>
                      <strong>
                        {item.calories_burned != null ? `${formatNumber(item.calories_burned)} kcal` : '—'}
                      </strong>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </section>
        </>
      )}
    </main>
  )
}
