import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api, macrosFromNutrients } from '../api'
import BarcodeScanner from '../components/BarcodeScanner'
import { formatNumber } from '../lib/format'
import { getSpeechRecognition, speechSupported } from '../lib/speech'

const MEALS = ['breakfast', 'lunch', 'dinner']

function normalizeMeal(value) {
  return MEALS.includes(value) ? value : 'dinner'
}

export default function AddFood() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [meal, setMeal] = useState(normalizeMeal(params.get('meal')))
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [frequent, setFrequent] = useState([])
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [grams, setGrams] = useState(100)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)
  const [searching, setSearching] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [listening, setListening] = useState(false)
  const [voiceNote, setVoiceNote] = useState('')
  const canSpeak = speechSupported()

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

  const chooseFood = useCallback(async (food, nextGrams) => {
    setSelected(food)
    setError('')
    setStatus(`Selected ${food.description}`)
    try {
      const data = await api.foodDetail(food.fdc_id)
      setDetail(data)
      setGrams(nextGrams || food.grams || 100)
    } catch (err) {
      setDetail(null)
      setError(err.message)
    }
  }, [])

  const lookupBarcode = useCallback(async (code) => {
    setScanning(false)
    setSearching(true)
    setError('')
    setStatus(`Looking up barcode ${code}…`)
    try {
      const data = await api.lookupBarcode(code)
      setQuery(code)
      setResults(data.foods || [])
      if (data.foods?.[0]) {
        await chooseFood(data.foods[0])
        setStatus(data.product_hint
          ? `Matched via ${data.product_hint}`
          : 'Barcode matched. Adjust grams, then add.')
      }
    } catch (err) {
      setError(err.message)
      setStatus('')
    } finally {
      setSearching(false)
    }
  }, [chooseFood])

  const applyTranscript = useCallback(async (transcript, { autoLog = false, defaultMeal = meal } = {}) => {
    const text = String(transcript || '').trim()
    if (!text) return
    setVoiceNote(text)
    setStatus(`Heard: “${text}”`)
    setError('')
    try {
      if (autoLog) {
        const result = await api.logFromVoice({
          transcript: text,
          default_meal: defaultMeal,
          auto_log: true,
        })
        setMeal(normalizeMeal(result.meal))
        setQuery(result.food_query)
        setGrams(result.grams)
        setResults(result.foods || [])
        if (result.selected) await chooseFood(result.selected, result.grams)
        setStatus(`Logged ${result.selected?.description || result.food_query} · ${result.grams} g · ${normalizeMeal(result.meal)}`)
        window.setTimeout(() => navigate('/app'), 700)
        return
      }
      const parsed = await api.parseVoice({ transcript: text, default_meal: defaultMeal })
      setMeal(normalizeMeal(parsed.meal))
      setQuery(parsed.food_query)
      setGrams(parsed.grams)
      setResults(parsed.foods || [])
      if (parsed.foods?.[0]) {
        await chooseFood(parsed.foods[0], parsed.grams)
        setStatus(`Ready to log ${parsed.foods[0].description} · ${parsed.grams} g · ${normalizeMeal(parsed.meal)}`)
      } else {
        setStatus(`Understood “${parsed.food_query}” (${parsed.grams} g). Pick a match below.`)
      }
    } catch (err) {
      setError(err.message)
    }
  }, [chooseFood, meal, navigate])

  useEffect(() => {
    const transcript = params.get('transcript') || params.get('say') || params.get('q')
    const barcode = params.get('barcode')
    const autoLog = params.get('auto_log') === '1' || params.get('autolog') === '1'
    const speak = params.get('speak') === '1'
    if (barcode) {
      lookupBarcode(barcode)
      return
    }
    if (transcript) {
      applyTranscript(transcript, { autoLog })
      return
    }
    if (speak) {
      // Defer so the page paints before the mic permission prompt.
      window.setTimeout(() => {
        const recognition = getSpeechRecognition()
        if (!recognition) {
          setError('Voice logging needs a browser with speech recognition (Chrome works best).')
          return
        }
        setListening(true)
        setStatus('Listening… tell me what you ate.')
        recognition.onresult = (event) => {
          const heard = event.results?.[0]?.[0]?.transcript || ''
          setListening(false)
          applyTranscript(heard, { autoLog })
        }
        recognition.onerror = () => {
          setListening(false)
          setError('Could not hear that. Try again, or type the food.')
        }
        recognition.onend = () => setListening(false)
        recognition.start()
      }, 250)
    }
    // Run once for deep-link / assistant handoff params.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleVoice() {
    const recognition = getSpeechRecognition()
    if (!recognition) {
      setError('Voice logging needs a browser with speech recognition (Chrome works best).')
      return
    }
    setError('')
    setVoiceNote('')
    setListening(true)
    setStatus('Listening… tell me what you ate.')
    recognition.onresult = async (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || ''
      setListening(false)
      await applyTranscript(transcript)
    }
    recognition.onerror = () => {
      setListening(false)
      setError('Could not hear that. Try again, or type the food.')
    }
    recognition.onend = () => setListening(false)
    recognition.start()
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
          placeholder="Search foods or paste a barcode"
          aria-label="Search foods"
        />
      </div>

      <div className="action-row">
        <button type="button" className="action-chip" onClick={() => setScanning(true)}>
          Scan barcode
        </button>
        <button
          type="button"
          className={`action-chip ${listening ? 'is-live' : ''}`}
          onClick={handleVoice}
          disabled={listening}
        >
          {listening ? 'Listening…' : canSpeak ? 'Speak what you ate' : 'Voice unavailable'}
        </button>
      </div>

      {scanning && (
        <BarcodeScanner
          onDetected={lookupBarcode}
          onClose={() => setScanning(false)}
        />
      )}

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

      {voiceNote && <p className="voice-note">“{voiceNote}”</p>}
      {status && <p className="status-note">{status}</p>}
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
          <p className="muted">Search, scan a barcode, or say something like “180 grams of chicken for dinner”.</p>
        ) : (
          <ul className="result-list">
            {results.map((food) => (
              <li key={food.fdc_id}>
                <button type="button" onClick={() => chooseFood(food)}>
                  <span>{food.description}</span>
                  <small>{food.brand_name || food.data_type || 'Food'}{food.gtin_upc ? ` · ${food.gtin_upc}` : ''}</small>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}
