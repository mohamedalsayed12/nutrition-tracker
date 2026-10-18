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
  setNutrition: (payload) => request('/api/v1/goals/nutrition', { method: 'PUT', body: payload }),
  setMacroSplit: (payload) => request('/api/v1/settings/macro-split', { method: 'PUT', body: payload }),
  getNutrition: () => request('/api/v1/goals/nutrition'),
  getMacroSplit: () => request('/api/v1/settings/macro-split'),

  dailyReport: (date) => request(`/api/v1/reports/daily${date ? `?date=${date}` : ''}`),
  weeklyReport: () => request('/api/v1/reports/weekly'),
  foodLogs: () => request('/api/v1/food-logs?per_page=100'),
  createFoodLog: (payload) => request('/api/v1/food-logs', { method: 'POST', body: payload }),
  deleteFoodLog: (id) => request(`/api/v1/food-logs/${id}`, { method: 'DELETE' }),
  searchFoods: (q) => request(`/api/v1/foods?q=${encodeURIComponent(q)}`),
  foodDetail: (fdcId) => request(`/api/v1/foods/${fdcId}`),
  lookupBarcode: (code) => request(`/api/v1/foods/barcode/${encodeURIComponent(code)}`),
  parseVoice: (payload) => request('/api/v1/foods/voice-parse', { method: 'POST', body: payload }),
  logFromVoice: (payload) => request('/api/v1/food-logs/from-voice', { method: 'POST', body: payload }),
  frequentFoods: () => request('/api/v1/foods/frequent'),
}

export function nutrientAmount(nutrients, names) {
  const wanted = names.map((name) => name.toLowerCase())
  for (const item of nutrients || []) {
    const name = String(item.name || '').toLowerCase()
    const unit = String(item.unit || '').toLowerCase()
    if (!wanted.some((part) => name.includes(part))) continue
    const amount = Number(item.eaten ?? item.per_100g ?? item.amount)
    if (!Number.isFinite(amount)) continue
    if (wanted.includes('energy') || wanted.includes('calorie')) {
      if (unit === 'kcal') return amount
      continue
    }
    if (unit === 'g' || unit === 'mg' || unit === 'mcg' || unit === 'µg') return amount
    return amount
  }
  return 0
}

export function macrosFromNutrients(nutrients) {
  return {
    calories: nutrientAmount(nutrients, ['energy']),
    protein: nutrientAmount(nutrients, ['protein']),
    carbs: nutrientAmount(nutrients, ['carbohydrate']),
    fat: nutrientAmount(nutrients, ['lipid', 'total fat', 'fat']),
  }
}
