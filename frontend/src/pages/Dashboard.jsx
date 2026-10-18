import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, clearToken } from '../api'
import MacroBar from '../components/MacroBar'

export default function Dashboard() {
  const navigate = useNavigate()
  const [me, setMe] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const profile = await api.me()
        if (!active) return
        if (profile.needs_goal) {
          navigate('/goal')
          return
        }
        setMe(profile)
        const daily = await api.dailyReport()
        if (!active) return
        setReport(daily)
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

  function logout() {
    clearToken()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <MacroBar progress={report?.progress || []} loading={loading} />
      <main className="dashboard">
        <section className="dashboard-hero">
          <p className="eyebrow">Harvest</p>
          <h1>{me ? `Hi, ${me.name}` : 'Your day'}</h1>
          <p className="lede">
            The bar above fills as you approach each macro target. Keep logging meals to watch it grow.
          </p>
          <button type="button" className="btn-ghost" onClick={logout}>Sign out</button>
        </section>

        {error && <p className="form-error" role="alert">{error}</p>}

        <section className="dashboard-panel">
          <h2>Today at a glance</h2>
          {loading && <p>Loading your targets…</p>}
          {!loading && report && (
            <ul className="stat-list">
              <li><span>Calories</span><strong>{report.calorie_goal ?? '—'} kcal goal</strong></li>
              <li><span>Food logs</span><strong>{report.food_log_count}</strong></li>
              <li><span>Protein target</span><strong>{report.protein_min}–{report.protein_max} g</strong></li>
              <li><span>Carb target</span><strong>{report.carbs} g</strong></li>
            </ul>
          )}
          {!loading && report?.progress?.length > 0 && (
            <div className="progress-cards">
              {report.progress.map((row) => (
                <article key={row.name} className="progress-card">
                  <h3>{row.name}</h3>
                  <p>{row.logged == null ? 'Nothing logged yet' : `${row.logged} ${row.unit}`}</p>
                  <p className="progress-card__target">Target {row.target_label}</p>
                  <div className="macro-track__rail">
                    <div
                      className={`macro-track__fill macro-track__fill--${row.name.toLowerCase()}`}
                      style={{ width: `${Math.max(0, Math.min(row.percent ?? 0, 100))}%` }}
                    />
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
