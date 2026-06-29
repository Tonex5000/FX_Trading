/**
 * API Service — all HTTP calls to the FastAPI backend.
 * The frontend never talks to OANDA, ForexFactory, or Anthropic directly.
 * Everything goes through http://localhost:8000 (or VITE_API_URL).
 */

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err?.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

/** GET /api/market — live OANDA price + indicators */
export const getMarket = () => request('/api/market')

/** GET /api/news — ForexFactory calendar */
export const getNews = () => request('/api/news')

/**
 * POST /api/analyze — full AI signal
 * @param {number} accountBalance
 */
export const analyze = (accountBalance) =>
  request('/api/analyze', {
    method: 'POST',
    body:   JSON.stringify({ account_balance: accountBalance }),
  })

/** GET /health — server health check */
export const healthCheck = () => request('/health')
