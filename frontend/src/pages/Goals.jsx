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

const HEALTH_CONDITIONS = [
  { id: 'pregnancy', label: 'Pregnancy' },
  { id: 'diabetes', label: 'Diabetes' },
  { id: 'ibs', label: 'IBS' },
  { id: 'menstruation', label: 'Periods / menstruation' },
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
  const [conditions, setConditions] = useState([])
  const [trimester, setTrimester] = useState(2)
  const [guidance, setGuidance] = useState([])
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    async function load() {
      try {
        const [me, nutrition, health] = await Promise.all([
          api.me(),
          api.getNutrition(),
          api.getHealth().catch(() => ({ conditions: [], trimester: null, guidance: [] })),
        ])
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
        setConditions(health.conditions || [])
        setTrimester(health.trimester || 2)
        setGuidance(health.guidance || [])
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

  function toggleCondition(id) {
    setConditions((current) => {
      const has = current.includes(id)
      let next = has ? current.filter((item) => item !== id) : [...current, id]
      if (id === 'pregnancy' && !has) {
        next = next.filter((item) => item !== 'menstruation')
      }
      if (id === 'menstruation' && !has) {
        next = next.filter((item) => item !== 'pregnancy')
      }
      return next
    })
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

  const visibleConditions = HEALTH_CONDITIONS.filter((item) => {
    if (item.id === 'pregnancy' || item.id === 'menstruation') {
      return form.sex === 'female'
    }
    return true
  })

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

      const healthPayload = {
        conditions: form.sex === 'female'
          ? conditions
          : conditions.filter((item) => item !== 'pregnancy' && item !== 'menstruation'),
        trimester: conditions.includes('pregnancy') ? Number(trimester) : null,
      }
      const health = await api.setHealth(healthPayload)
      setConditions(health.conditions || [])
      setTrimester(health.trimester || 2)
      setGuidance(health.guidance || [])
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
                  onClick={() => {
                    update('sex', sex)
                    if (sex === 'male') {
                      setConditions((current) => current.filter(
                        (item) => item !== 'pregnancy' && item !== 'menstruation',
                      ))
                    }
                  }}
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

          <section className="card">
            <label className="field-label">Conditions</label>
            <p className="muted hint-line">
              Adjusts micronutrient guidance for pregnancy, diabetes, IBS, and periods.
            </p>
            <div className="condition-list">
              {visibleConditions.map((item) => (
                <label key={item.id} className="check-row">
                  <input
                    type="checkbox"
                    checked={conditions.includes(item.id)}
                    onChange={() => toggleCondition(item.id)}
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>

            {conditions.includes('pregnancy') && form.sex === 'female' && (
              <>
                <label className="field-label">Trimester</label>
                <div className="segmented">
                  {[1, 2, 3].map((value) => (
                    <button
                      key={value}
                      type="button"
                      className={Number(trimester) === value ? 'is-active' : ''}
                      onClick={() => setTrimester(value)}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </>
            )}

            {guidance.length > 0 && (
              <ul className="guidance-list">
                {guidance.map((item) => (
                  <li key={item.label}>
                    <strong>{item.label}</strong>
                    <span>{item.summary}</span>
                  </li>
                ))}
              </ul>
            )}
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
