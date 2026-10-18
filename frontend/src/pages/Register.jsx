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
  age: 30,
  sex: 'female',
  height_cm: 165,
  weight_kg: 60,
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
      navigate('/goal')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-panel auth-panel--wide">
        <p className="eyebrow">Harvest</p>
        <h1>Create your plate</h1>
        <p className="lede">Tell us your body metrics so we can shape calorie and macro targets around you.</p>
        <form className="stack-form" onSubmit={onSubmit}>
          <label>
            Name
            <input value={form.name} onChange={(e) => update('name', e.target.value)} required maxLength={100} />
          </label>
          <label>
            Email
            <input type="email" value={form.email} onChange={(e) => update('email', e.target.value)} required />
          </label>
          <label>
            Password
            <input type="password" value={form.password} onChange={(e) => update('password', e.target.value)} required minLength={8} />
          </label>
          <div className="form-grid">
            <label>
              Age
              <input type="number" min={18} max={100} value={form.age} onChange={(e) => update('age', e.target.value)} required />
            </label>
            <label>
              Gender
              <select value={form.sex} onChange={(e) => update('sex', e.target.value)}>
                <option value="female">Female</option>
                <option value="male">Male</option>
              </select>
            </label>
            <label>
              Height (cm)
              <input type="number" min={50} max={300} step="0.1" value={form.height_cm} onChange={(e) => update('height_cm', e.target.value)} required />
            </label>
            <label>
              Weight (kg)
              <input type="number" min={20} max={500} step="0.1" value={form.weight_kg} onChange={(e) => update('weight_kg', e.target.value)} required />
            </label>
          </div>
          <label>
            Activity level
            <select value={form.activity_level} onChange={(e) => update('activity_level', e.target.value)}>
              {ACTIVITY.map((level) => (
                <option key={level} value={level}>{level}</option>
              ))}
            </select>
          </label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="btn-primary" type="submit" disabled={busy}>{busy ? 'Creating…' : 'Continue'}</button>
        </form>
        <p className="auth-switch">Already tracking? <Link to="/login">Sign in</Link></p>
      </section>
    </main>
  )
}
