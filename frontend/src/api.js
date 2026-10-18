const TOKEN_KEY = 'harvest_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth) {
    const token = getToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }
  const response = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  const text = await response.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = { error: text || 'Unexpected response' }
  }
  if (!response.ok) {
    const message = data?.error || data?.description || data?.msg || 'Request failed'
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return data
}

export const api = {
  register: (payload) => request('/api/v1/users', { method: 'POST', body: payload, auth: false }),
  login: (payload) => request('/api/v1/auth/login', { method: 'POST', body: payload, auth: false }),
  me: () => request('/api/v1/users/me'),
  setGoal: (goal) => request('/api/v1/goals/goal', { method: 'PUT', body: { goal } }),
  dailyReport: (date) => request(`/api/v1/reports/daily${date ? `?date=${date}` : ''}`),
}
