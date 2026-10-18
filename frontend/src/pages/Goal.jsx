import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const GOALS = [
  {
    id: 'lose_weight',
    title: 'Lose weight',
    copy: 'A gentle calorie deficit with protein kept high enough to protect lean mass.',
  },
  {
    id: 'maintain',
    title: 'Maintain',
    copy: 'Match your estimated daily energy needs and keep macros balanced.',
  },
  {
    id: 'gain_weight',
    title: 'Gain weight',
    copy: 'A modest surplus so you can build with room for carbs and protein.',
  },
]

export default function Goal() {
  const navigate = useNavigate()
  const [goal, setGoal] = useState('maintain')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)

  async function onSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const data = await api.setGoal(goal)
      setResult(data)
      window.setTimeout(() => navigate('/app'), 900)
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-panel auth-panel--wide">
        <p className="eyebrow">Almost ready</p>
        <h1>What is your goal?</h1>
        <p className="lede">We use your registration metrics to set calories and macros for this goal.</p>
        <form className="goal-form" onSubmit={onSubmit}>
          <div className="goal-grid">
            {GOALS.map((option) => (
              <button
                key={option.id}
                type="button"
                className={`goal-card ${goal === option.id ? 'is-selected' : ''}`}
                onClick={() => setGoal(option.id)}
              >
                <strong>{option.title}</strong>
                <span>{option.copy}</span>
              </button>
            ))}
          </div>
          {error && <p className="form-error" role="alert">{error}</p>}
          {result && (
            <p className="goal-result" role="status">
              Targets set: {result.calories} kcal · protein {result.protein_min}–{result.protein_max} g · carbs {result.carbs} g
            </p>
          )}
          <button className="btn-primary" type="submit" disabled={busy}>
            {busy ? 'Calculating…' : 'Set my targets'}
          </button>
        </form>
      </section>
    </main>
  )
}
