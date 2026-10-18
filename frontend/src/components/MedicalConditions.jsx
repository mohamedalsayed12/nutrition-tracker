import { useState } from 'react'
import { api } from '../api'

export const MEDICAL_CONDITIONS = [
  { id: 'menstruation', label: 'Period', femaleOnly: true },
  { id: 'pregnancy', label: 'Pregnancy', femaleOnly: true },
  { id: 'diabetes', label: 'Diabetes', femaleOnly: false },
  { id: 'ibs', label: 'IBS', femaleOnly: false },
]

export default function MedicalConditions({
  sex,
  conditions,
  trimester,
  guidance = [],
  onChange,
  compact = false,
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const visible = MEDICAL_CONDITIONS.filter((item) => {
    if (item.femaleOnly && sex !== 'female') return false
    return true
  })

  async function save(nextConditions, nextTrimester = trimester) {
    setBusy(true)
    setError('')
    try {
      const payload = {
        conditions: nextConditions,
        trimester: nextConditions.includes('pregnancy') ? Number(nextTrimester || 2) : null,
      }
      const health = await api.setHealth(payload)
      // Period is managed as a health condition now, not a separate day toggle.
      if (!nextConditions.includes('menstruation')) {
        const now = new Date()
        const day = [
          now.getFullYear(),
          String(now.getMonth() + 1).padStart(2, '0'),
          String(now.getDate()).padStart(2, '0'),
        ].join('-')
        await api.clearDayConditions(day).catch(() => null)
      }
      onChange?.({
        conditions: health.conditions || [],
        trimester: health.trimester || 2,
        guidance: health.guidance || [],
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function toggle(id) {
    if (busy) return
    const has = conditions.includes(id)
    let next = has ? conditions.filter((item) => item !== id) : [...conditions, id]
    if (id === 'pregnancy' && !has) {
      next = next.filter((item) => item !== 'menstruation')
    }
    if (id === 'menstruation' && !has) {
      next = next.filter((item) => item !== 'pregnancy')
    }
    save(next, trimester)
  }

  function setTrimesterValue(value) {
    if (busy || !conditions.includes('pregnancy')) return
    save(conditions, value)
  }

  return (
    <section className={`card conditions-card ${compact ? 'is-compact' : ''}`}>
      <h2>Medical conditions</h2>
      <p className="muted hint-line">
        Adjusts nutrient targets for period, pregnancy, diabetes, IBS, and related needs.
      </p>

      <div className="condition-list">
        {visible.map((item) => (
          <label key={item.id} className="check-row">
            <input
              type="checkbox"
              checked={conditions.includes(item.id)}
              disabled={busy}
              onChange={() => toggle(item.id)}
            />
            <span>{item.label}</span>
          </label>
        ))}
      </div>

      {conditions.includes('pregnancy') && sex === 'female' && (
        <>
          <p className="field-label">Trimester</p>
          <div className="segmented">
            {[1, 2, 3].map((value) => (
              <button
                key={value}
                type="button"
                className={Number(trimester) === value ? 'is-active' : ''}
                disabled={busy}
                onClick={() => setTrimesterValue(value)}
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

      {error && <p className="banner-error">{error}</p>}
    </section>
  )
}
