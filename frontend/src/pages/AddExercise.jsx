import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, clearToken } from '../api'
import { formatNumber } from '../lib/format'

const ACTIVITY_TYPES = [
  ['walking', 'Walking'],
  ['running', 'Running'],
  ['cycling', 'Cycling'],
  ['swimming', 'Swimming'],
  ['strength', 'Strength'],
  ['yoga', 'Yoga'],
  ['other_light', 'Other light'],
  ['other_moderate', 'Other moderate'],
  ['other_vigorous', 'Other vigorous'],
]

const INITIAL = {
  activity: '',
  activity_type: 'walking',
  duration_minutes: 30,
  weight_kg: 70,
  height_cm: 170,
  extra: true,
}

export default function AddExercise() {
  const navigate = useNavigate()
  const [form, setForm] = useState(INITIAL)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    async function load() {
      try {
        const [me, nutrition] = await Promise.all([api.me(), api.getNutrition()])
        if (!active) return
        const profile = me.profile || {}
        setForm((current) => ({
          ...current,
          weight_kg: nutrition.weight_kg || profile.weight_kg || current.weight_kg,
          height_cm: nutrition.height_cm || profile.height_cm || current.height_cm,
        }))
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

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function save(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const label = form.activity.trim()
        || ACTIVITY_TYPES.find(([value]) => value === form.activity_type)?.[1]
        || 'Exercise'
      await api.createActivityLog({
        activity: label,
        activity_type: form.activity_type,
        duration_minutes: Number(form.duration_minutes),
        weight_kg: Number(form.weight_kg),
        height_cm: Number(form.height_cm),
        extra: Boolean(form.extra),
      })
      navigate('/app')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="screen">
      <header className="screen-header">
        <h1>Add exercise</h1>
      </header>

      {loading ? <p className="muted">Loading…</p> : (
        <form className="goals-form" onSubmit={save}>
          <section className="card">
            <label>
              Activity name
              <input
                value={form.activity}
                onChange={(e) => update('activity', e.target.value)}
                placeholder="Morning walk"
                maxLength={200}
              />
            </label>

            <label className="field-label">Type</label>
            <div className="chip-row wrap-chips">
              {ACTIVITY_TYPES.map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  className={`chip ${form.activity_type === value ? 'is-active' : ''}`}
                  onClick={() => update('activity_type', value)}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="triple-grid">
              <label>
                Minutes
                <input
                  type="number"
                  min="1"
                  max="1440"
                  step="1"
                  value={form.duration_minutes}
                  onChange={(e) => update('duration_minutes', e.target.value)}
                  required
                />
              </label>
              <label>
                Weight kg
                <input
                  type="number"
                  min="10"
                  max="500"
                  step="0.1"
                  value={form.weight_kg}
                  onChange={(e) => update('weight_kg', e.target.value)}
                  required
                />
              </label>
              <label>
                Height cm
                <input
                  type="number"
                  min="50"
                  max="300"
                  value={form.height_cm}
                  onChange={(e) => update('height_cm', e.target.value)}
                  required
                />
              </label>
            </div>

            <label className="check-row">
              <input
                type="checkbox"
                checked={form.extra}
                onChange={(e) => update('extra', e.target.checked)}
              />
              <span>Count toward today’s calorie target</span>
            </label>
            <p className="muted hint-line">
              Estimated burn uses your weight, height, age, and activity type
              (~{formatNumber(form.duration_minutes, 0)} min).
            </p>
          </section>

          {error && <p className="banner-error">{error}</p>}

          <button className="btn-green" type="submit" disabled={busy}>
            {busy ? 'Saving…' : 'Log exercise'}
          </button>
        </form>
      )}
    </main>
  )
}
