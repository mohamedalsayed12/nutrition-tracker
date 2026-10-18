import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api, macrosFromNutrients } from '../api'
import { formatNumber } from '../lib/format'

const MEALS = ['breakfast', 'lunch', 'dinner', 'snack']

export default function AddFood() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [meal, setMeal] = useState(params.get('meal') || 'dinner')
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [frequent, setFrequent] = useState([])
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [grams, setGrams] = useState(100)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [searching, setSearching] = useState(false)

  useEffect(() => {
    api.frequentFoods()
      .then((data) => {
        const items = Object.values(data.foods || {}).flat()
        const unique = []
        const seen = new Set()
        for (const item of items) {
          if (seen.has(item.fdc_id)) continue
          seen.add(item.fdc_id)
          unique.push(item)
        }
        setFrequent(unique.slice(0, 6))
      })
      .catch(() => setFrequent([]))
  }, [])

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([])
      return undefined
    }
    const handle = window.setTimeout(async () => {
      setSearching(true)
      setError('')
      try {
        const data = await api.searchFoods(query.trim())
        setResults(data.foods || [])
      } catch (err) {
        setError(err.message)
        setResults([])
      } finally {
        setSearching(false)
      }
    }, 280)
    return () => window.clearTimeout(handle)
  }, [query])

  async function chooseFood(food) {
    setSelected(food)
    setError('')
    try {
      const data = await api.foodDetail(food.fdc_id)
      setDetail(data)
      setGrams(food.grams || 100)
    } catch (err) {
      setDetail(null)
      setError(err.message)
    }
  }

  const portion = useMemo(() => {
    if (!detail) return { calories: 0, protein: 0, carbs: 0, fat: 0 }
    const per100 = macrosFromNutrients(detail.nutrients)
    const factor = Number(grams) / 100
    return {
      calories: per100.calories * factor,
      protein: per100.protein * factor,
      carbs: per100.carbs * factor,
      fat: per100.fat * factor,
    }
  }, [detail, grams])

  const per100 = detail ? macrosFromNutrients(detail.nutrients) : null
  const proteinPer100kcal = per100 && per100.calories > 0
    ? (per100.protein / per100.calories) * 100
    : null

  async function addFood(event) {
    event.preventDefault()
    if (!selected) return
    setBusy(true)
    setError('')
    try {
      await api.createFoodLog({
        meal,
        fdc_id: selected.fdc_id,
        grams: Number(grams),
      })
      navigate('/app')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="screen">
      <header className="screen-header">
        <h1>Add food</h1>
      </header>

      <div className="search-box">
        <span aria-hidden="true">⌕</span>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search foods"
          aria-label="Search foods"
        />
      </div>

      <div className="meal-pills" role="tablist" aria-label="Meal">
        {MEALS.map((item) => (
          <button
            key={item}
            type="button"
            role="tab"
            aria-selected={meal === item}
            className={meal === item ? 'is-active' : ''}
            onClick={() => setMeal(item)}
          >
            {item[0].toUpperCase() + item.slice(1)}
          </button>
        ))}
      </div>

      {frequent.length > 0 && (
        <div className="chip-row">
          {frequent.map((item) => (
            <button key={item.fdc_id} type="button" className="chip" onClick={() => chooseFood(item)}>
              {item.description}
            </button>
          ))}
        </div>
      )}

      {error && <p className="banner-error">{error}</p>}
      {searching && <p className="muted">Searching…</p>}

      {detail && selected && (
        <form className="card food-detail" onSubmit={addFood}>
          <h2>{detail.description || selected.description}</h2>
          <p className="muted">
            {formatNumber(per100?.calories, 0)} kcal / 100 g
            {proteinPer100kcal != null && ` · ${formatNumber(proteinPer100kcal, 1)} g protein / 100 kcal`}
          </p>
          <div className="qty-row">
            <button type="button" onClick={() => setGrams((value) => Math.max(5, Number(value) - 10))}>-</button>
            <label>
              <input
                type="number"
                min="1"
                max="10000"
                value={grams}
                onChange={(e) => setGrams(e.target.value)}
              />
              <span>g</span>
            </label>
            <button type="button" onClick={() => setGrams((value) => Math.min(10000, Number(value) + 10))}>+</button>
          </div>
          <div className="macro-grid">
            <div><strong>{formatNumber(portion.calories)}</strong><span>kcal</span></div>
            <div><strong>{formatNumber(portion.protein, 1)}</strong><span>protein</span></div>
            <div><strong>{formatNumber(portion.carbs, 1)}</strong><span>carbs</span></div>
            <div><strong>{formatNumber(portion.fat, 1)}</strong><span>fat</span></div>
          </div>
          <button className="btn-green" type="submit" disabled={busy}>
            {busy ? 'Adding…' : `Add to ${meal}`}
          </button>
        </form>
      )}

      <section className="card results-card">
        <h2>More results</h2>
        {results.length === 0 ? (
          <p className="muted">Search to find foods from USDA FoodData Central.</p>
        ) : (
          <ul className="result-list">
            {results.map((food) => (
              <li key={food.fdc_id}>
                <button type="button" onClick={() => chooseFood(food)}>
                  <span>{food.description}</span>
                  <small>{food.data_type || 'Food'}</small>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}
