import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, clearToken } from '../api'
import { formatNumber } from '../lib/format'

const ACTIVITY = [
  'sedentary',
  'lightly active',
  'moderately active',
  'very active',
  'extra active',
]

const INITIAL = {
  age: 22,
  sex: 'male',
  height_cm: 175,
  weight_kg: 75,
  activity_level: 'moderately active',
  goal: 'maintain',
}

export default function Goals() {
  const navigate = useNavigate()
  const [form, setForm] = useState(INITIAL)
  const [preview, setPreview] = useState(null)
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
        setForm({
          age: nutrition.age || profile.age || INITIAL.age,
          sex: nutrition.sex || profile.sex || INITIAL.sex,
          height_cm: nutrition.height_cm || profile.height_cm || INITIAL.height_cm,
          weight_kg: nutrition.weight_kg || profile.weight_kg || INITIAL.weight_kg,
          activity_level: nutrition.activity_level || profile.activity_level || INITIAL.activity_level,
          goal: nutrition.goal || profile.goal || (me.needs_goal ? 'maintain' : 'maintain'),
        })
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
    setPreview(null)
  }

  const macros = useMemo(() => {
    if (!preview) return null
    const calories = preview.calories
    const proteinPct = 25
    const carbsPct = 45
    const fatPct = 30
    const protein = calories * proteinPct / 100 / 4
    const carbs = calories * carbsPct / 100 / 4
    const fat = calories * fatPct / 100 / 9
    return { calories, protein, proteinPct, carbs, carbsPct, fat, fatPct }
  }, [preview])

  async function save(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const payload = {
        age: Number(form.age),
        sex: form.sex,
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        activity_level: form.activity_level,
        goal: form.goal,
      }
      const result = await api.setNutrition(payload)
      await api.setMacroSplit({
        carbs_percent: 45,
        protein_percent: 25,
        fat_percent: 30,
      })
      setPreview(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="screen">
      <header className="screen-header">
        <h1>Goals setup</h1>
      </header>

      {loading ? <p className="muted">Loading profile…</p> : (
        <form className="goals-form" onSubmit={save}>
          <section className="card">
            <label className="field-label">Sex</label>
            <div className="segmented">
              {['male', 'female'].map((sex) => (
                <button
                  key={sex}
                  type="button"
                  className={form.sex === sex ? 'is-active' : ''}
                  onClick={() => update('sex', sex)}
                >
                  {sex[0].toUpperCase() + sex.slice(1)}
                </button>
              ))}
            </div>

            <div className="triple-grid">
              <label>
                Age
                <input type="number" min="18" max="100" value={form.age} onChange={(e) => update('age', e.target.value)} />
              </label>
              <label>
                Height cm
                <input type="number" min="50" max="300" value={form.height_cm} onChange={(e) => update('height_cm', e.target.value)} />
              </label>
              <label>
                Weight kg
                <input type="number" min="20" max="500" step="0.1" value={form.weight_kg} onChange={(e) => update('weight_kg', e.target.value)} />
              </label>
            </div>

            <label>
              Activity level
              <select value={form.activity_level} onChange={(e) => update('activity_level', e.target.value)}>
                {ACTIVITY.map((level) => (
                  <option key={level} value={level}>{level[0].toUpperCase() + level.slice(1)}</option>
                ))}
              </select>
            </label>

            <label className="field-label">Goal</label>
            <div className="segmented">
              {[
                ['lose_weight', 'Lose'],
                ['maintain', 'Maintain'],
                ['gain_weight', 'Gain'],
              ].map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  className={form.goal === value ? 'is-active' : ''}
                  onClick={() => update('goal', value)}
                >
                  {label}
                </button>
              ))}
            </div>
          </section>

          {error && <p className="banner-error">{error}</p>}

          <section className="target-card">
            <p>Daily target</p>
            <strong className="target-card__kcal">
              {macros ? formatNumber(macros.calories) : '—'} <span>kcal</span>
            </strong>
            <div className="target-macros">
              <span>Protein {macros?.proteinPct ?? '—'}% ({macros ? formatNumber(macros.protein, 0) : '—'} g)</span>
              <span>Carbs {macros?.carbsPct ?? '—'}% ({macros ? formatNumber(macros.carbs, 0) : '—'} g)</span>
              <span>Fat {macros?.fatPct ?? '—'}% ({macros ? formatNumber(macros.fat, 0) : '—'} g)</span>
            </div>
            <button className="btn-green" type="submit" disabled={busy}>
              {busy ? 'Saving…' : 'Save targets'}
            </button>
          </section>
        </form>
      )}
    </main>
  )
}
