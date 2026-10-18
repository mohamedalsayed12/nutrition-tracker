import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, setToken } from '../api'

const ACTIVITY = [
  'sedentary',
  'lightly active',
  'moderately active',
  'very active',
  'extra active',
]

const INITIAL = {
  name: '',
  email: '',
  password: '',
  age: 22,
  sex: 'male',
  height_cm: 175,
  weight_kg: 75,
  activity_level: 'moderately active',
}

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState(INITIAL)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function onSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await api.register({
        ...form,
        age: Number(form.age),
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
      })
      const login = await api.login({ email: form.email, password: form.password })
      setToken(login.access_token)
      navigate('/app/goals')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="phone-frame">
      <main className="phone-screen auth-screen">
        <p className="brand">Nutrition tracker</p>
        <h1>Create account</h1>
        <form className="stack" onSubmit={onSubmit}>
          <label>Name<input value={form.name} onChange={(e) => update('name', e.target.value)} required /></label>
          <label>Email<input type="email" value={form.email} onChange={(e) => update('email', e.target.value)} required /></label>
          <label>Password<input type="password" value={form.password} onChange={(e) => update('password', e.target.value)} required minLength={8} /></label>
          <div className="segmented">
            {['male', 'female'].map((sex) => (
              <button key={sex} type="button" className={form.sex === sex ? 'is-active' : ''} onClick={() => update('sex', sex)}>
                {sex[0].toUpperCase() + sex.slice(1)}
              </button>
            ))}
          </div>
          <div className="triple-grid">
            <label>Age<input type="number" min="18" max="100" value={form.age} onChange={(e) => update('age', e.target.value)} /></label>
            <label>Height<input type="number" min="50" max="300" value={form.height_cm} onChange={(e) => update('height_cm', e.target.value)} /></label>
            <label>Weight<input type="number" min="20" max="500" step="0.1" value={form.weight_kg} onChange={(e) => update('weight_kg', e.target.value)} /></label>
          </div>
          <label>
            Activity
            <select value={form.activity_level} onChange={(e) => update('activity_level', e.target.value)}>
              {ACTIVITY.map((level) => <option key={level} value={level}>{level}</option>)}
            </select>
          </label>
          {error && <p className="banner-error">{error}</p>}
          <button className="btn-green" type="submit" disabled={busy}>{busy ? 'Creating…' : 'Continue'}</button>
        </form>
        <p className="auth-foot">Already tracking? <Link to="/login">Sign in</Link></p>
      </main>
    </div>
  )
}
