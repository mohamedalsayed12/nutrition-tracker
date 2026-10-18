import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, clearToken } from '../api'
import { formatNumber } from '../lib/format'

const INTENSITIES = [
  ['easy', 'Easy'],
  ['medium', 'Medium'],
  ['hard', 'Hard'],
]

const INITIAL = {
  query: '',
  duration_minutes: 30,
  intensity: 'medium',
  weight_kg: 70,
  height_cm: 170,
  extra: true,
}

export default function AddExercise() {
  const navigate = useNavigate()
  const [form, setForm] = useState(INITIAL)
  const [results, setResults] = useState([])
  const [selected, setSelected] = useState(null)
  const [estimate, setEstimate] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [searching, setSearching] = useState(false)
  const [estimating, setEstimating] = useState(false)
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
    if (field !== 'extra') setEstimate(null)
  }

  useEffect(() => {
    const query = form.query.trim()
    if (query.length < 2) {
      setResults([])
      return undefined
    }
    const handle = window.setTimeout(async () => {
      setSearching(true)
      setError('')
      try {
        const data = await api.searchExercises(query, {
          duration: form.duration_minutes,
          weight_kg: form.weight_kg,
        })
        setResults(data.exercises || [])
      } catch (err) {
        setError(err.message)
        setResults([])
      } finally {
        setSearching(false)
      }
    }, 280)
    return () => window.clearTimeout(handle)
  }, [form.query, form.duration_minutes, form.weight_kg])

  useEffect(() => {
    if (!selected) {
      setEstimate(null)
      return undefined
    }
    let active = true
    const handle = window.setTimeout(async () => {
      setEstimating(true)
      setError('')
      try {
        const data = await api.estimateExercise({
          activity: selected.name,
          duration_minutes: Number(form.duration_minutes),
          intensity: form.intensity,
          weight_kg: Number(form.weight_kg),
          height_cm: Number(form.height_cm),
        })
        if (active) setEstimate(data)
      } catch (err) {
        if (active) {
          setEstimate(null)
          setError(err.message)
        }
      } finally {
        if (active) setEstimating(false)
      }
    }, 200)
    return () => {
      active = false
      window.clearTimeout(handle)
    }
  }, [selected, form.duration_minutes, form.intensity, form.weight_kg, form.height_cm])

  function chooseExercise(item) {
    setSelected(item)
    setForm((current) => ({ ...current, query: item.name }))
    setResults([])
  }

  function clearSelection() {
    setSelected(null)
    setEstimate(null)
  }

  const previewKcal = useMemo(() => {
    if (estimate?.calories_burned != null) return estimate.calories_burned
    if (selected?.total_calories != null && form.intensity === 'medium') return selected.total_calories
    return null
  }, [estimate, selected, form.intensity])

  async function save(event) {
    event.preventDefault()
    if (!selected) {
      setError('Pick one exercise from the search results.')
      return
    }
    setBusy(true)
    setError('')
    try {
      await api.createActivityLog({
        activity: selected.name,
        duration_minutes: Number(form.duration_minutes),
        intensity: form.intensity,
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
              Search exercise
              <input
                value={form.query}
                onChange={(e) => {
                  update('query', e.target.value)
                  if (selected && e.target.value !== selected.name) clearSelection()
                }}
                placeholder="Running, cycling, yoga…"
                maxLength={80}
                autoComplete="off"
              />
            </label>

            {searching && <p className="muted">Searching API Ninjas…</p>}

            {!selected && results.length > 0 && (
              <ul className="result-list exercise-results">
                {results.map((item) => (
                  <li key={item.name}>
                    <button type="button" onClick={() => chooseExercise(item)}>
                      <span>{item.name}</span>
                      <small>
                        {item.total_calories != null
                          ? `${formatNumber(item.total_calories)} kcal · ${formatNumber(item.duration_minutes, 0)} min`
                          : 'Tap to select'}
                      </small>
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {selected && (
              <div className="selected-exercise">
                <div>
                  <p className="density-label">Selected</p>
                  <strong>{selected.name}</strong>
                </div>
                <button type="button" className="text-btn" onClick={clearSelection}>Change</button>
              </div>
            )}

            <label>
              Duration (minutes)
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

            <label className="field-label">Intensity</label>
            <div className="segmented" role="radiogroup" aria-label="Intensity">
              {INTENSITIES.map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  role="radio"
                  aria-checked={form.intensity === value}
                  className={form.intensity === value ? 'is-active' : ''}
                  onClick={() => update('intensity', value)}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="triple-grid">
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
              <label>
                Burn
                <input
                  value={estimating ? '…' : previewKcal != null ? `${formatNumber(previewKcal)} kcal` : '—'}
                  readOnly
                  aria-live="polite"
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
              Calories come from API Ninjas for your duration. Choose one exercise and one intensity.
            </p>
          </section>

          {error && <p className="banner-error">{error}</p>}

          <button className="btn-green" type="submit" disabled={busy || !selected}>
            {busy ? 'Saving…' : previewKcal != null ? `Log · ${formatNumber(previewKcal)} kcal` : 'Log exercise'}
          </button>
        </form>
      )}
    </main>
  )
}
