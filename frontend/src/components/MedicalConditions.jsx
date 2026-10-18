import { useState } from 'react'
import { api } from '../api'

export const MEDICAL_CONDITIONS = [
  { id: 'menstruation', label: 'Period', femaleOnly: true, group: 'Reproductive' },
  { id: 'pregnancy', label: 'Pregnancy', femaleOnly: true, group: 'Reproductive' },
  { id: 'lactation', label: 'Lactation / breastfeeding', femaleOnly: true, group: 'Reproductive' },
  { id: 'menopause', label: 'Menopause', femaleOnly: true, group: 'Reproductive' },
  { id: 'diabetes', label: 'Diabetes', femaleOnly: false, group: 'Metabolic' },
  { id: 'hypertension', label: 'Hypertension', femaleOnly: false, group: 'Metabolic' },
  { id: 'thyroid', label: 'Thyroid disorder', femaleOnly: false, group: 'Metabolic' },
  { id: 'ibs', label: 'IBS', femaleOnly: false, group: 'Digestive' },
  { id: 'celiac', label: 'Celiac disease', femaleOnly: false, group: 'Digestive' },
  { id: 'crohn_ibd', label: 'Crohn’s / IBD', femaleOnly: false, group: 'Digestive' },
  { id: 'bariatric', label: 'Bariatric surgery', femaleOnly: false, group: 'Digestive' },
  { id: 'vegan', label: 'Vegan', femaleOnly: false, group: 'Diet' },
  { id: 'vegetarian', label: 'Vegetarian', femaleOnly: false, group: 'Diet' },
  { id: 'anemia_iron', label: 'Iron-deficiency anemia', femaleOnly: false, group: 'Nutrient status' },
  { id: 'osteoporosis', label: 'Osteoporosis / bone loss', femaleOnly: false, group: 'Nutrient status' },
  { id: 'kidney_disease', label: 'Chronic kidney disease', femaleOnly: false, group: 'Nutrient status' },
]

const EXCLUSIVE_PAIRS = [
  ['pregnancy', 'menstruation'],
  ['pregnancy', 'lactation'],
  ['lactation', 'menstruation'],
]

function withoutConflicts(next, addedId) {
  let result = next
  for (const [a, b] of EXCLUSIVE_PAIRS) {
    if (addedId === a) result = result.filter((item) => item !== b)
    if (addedId === b) result = result.filter((item) => item !== a)
  }
  if (addedId === 'vegan') {
    // Vegan adjustments supersede vegetarian; keep UI tidy.
    result = result.filter((item) => item !== 'vegetarian')
  }
  return result
}

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
  const groups = [...new Set(visible.map((item) => item.group))]

  async function save(nextConditions, nextTrimester = trimester) {
    setBusy(true)
    setError('')
    try {
      const payload = {
        conditions: nextConditions,
        trimester: nextConditions.includes('pregnancy') ? Number(nextTrimester || 2) : null,
      }
      const health = await api.setHealth(payload)
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
    if (!has) next = withoutConflicts(next, id)
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
        Select every condition that should change your nutrient targets. Guidance updates instantly.
      </p>

      {groups.map((group) => (
        <div key={group} className="condition-group">
          <p className="density-label">{group}</p>
          <div className="condition-list">
            {visible.filter((item) => item.group === group).map((item) => (
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
        </div>
      ))}

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
            <li key={item.condition || item.label}>
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
