import { useState, useEffect, useCallback } from 'react'

const KEY = 'fx_ai_v2_journal'

export function useJournal() {
  const [entries, setEntries] = useState(() => {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]') } catch { return [] }
  })

  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify(entries)) } catch {}
  }, [entries])

  const add = useCallback((response) => {
    const { market, news, signal } = response
    const entry = {
      id: Date.now(), ts: new Date().toISOString(),
      signal: signal.signal, confidence: signal.confidence,
      regime: signal.regime, filters: signal.filters_passed,
      blocked_by: signal.blocked_by, rr: signal.risk_reward,
      risk_pct: signal.risk_percent, lots: signal.position_size_lots,
      entry: signal.entry_price, sl: signal.stop_loss, tp1: signal.take_profit_1,
      price: market.price.mid, adx: market.adx, atr: market.atr,
      trend_4h: market.trend_4h, trend_1h: market.trend_1h,
      session: market.session?.id, news_risk: news.risk?.level,
      outcome: null, pnl: null, notes: '',
    }
    setEntries(p => [entry, ...p].slice(0, 200))
    return entry
  }, [])

  const update = useCallback((id, outcome, pnl, notes) => {
    setEntries(p => p.map(e => e.id === id ? { ...e, outcome, pnl: +pnl || null, notes } : e))
  }, [])

  const clear = useCallback(() => {
    if (confirm('Clear all entries?')) setEntries([])
  }, [])

  const stats = (() => {
    const closed  = entries.filter(e => e.outcome && e.outcome !== 'NOT_TAKEN')
    const wins    = closed.filter(e => e.outcome === 'WIN')
    const losses  = closed.filter(e => e.outcome === 'LOSS')
    const pnlSum  = closed.reduce((s, e) => s + (e.pnl || 0), 0)
    const avgW    = wins.length   ? wins.reduce((s,e)=>s+(e.pnl||0),0)/wins.length : 0
    const avgL    = losses.length ? Math.abs(losses.reduce((s,e)=>s+(e.pnl||0),0)/losses.length) : 0
    return {
      total: entries.length,
      signals: entries.filter(e => e.signal !== 'NO TRADE').length,
      noTrade: entries.filter(e => e.signal === 'NO TRADE').length,
      closed: closed.length, wins: wins.length, losses: losses.length,
      winRate: closed.length ? Math.round(wins.length/closed.length*100) : null,
      pnl: +pnlSum.toFixed(2),
      pf: avgL > 0 ? +(avgW/avgL).toFixed(2) : null,
    }
  })()

  return { entries, add, update, clear, stats }
}
