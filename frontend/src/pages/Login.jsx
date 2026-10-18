import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, setToken } from '../api'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const login = await api.login({ email, password })
      setToken(login.access_token)
      const me = await api.me()
      navigate(me.needs_goal ? '/app/goals' : '/app')
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
        <h1>Welcome back</h1>
        <form className="stack" onSubmit={onSubmit}>
          <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
          <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
          {error && <p className="banner-error">{error}</p>}
          <button className="btn-green" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
        </form>
        <p className="auth-foot">New here? <Link to="/register">Create an account</Link></p>
      </main>
    </div>
  )
}
