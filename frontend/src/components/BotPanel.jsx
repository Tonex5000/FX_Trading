import { useState, useEffect, useCallback } from 'react'
import { StatBox, Panel, SectionLabel, Tag, Alert } from './UI'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function api(path, method = 'GET', body = null) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : null,
  })
  if (!res.ok) {
    const e = await res.json().catch(() => ({}))
    throw new Error(e.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

const ACTION_TAG = {
  ORDER_PLACED:        { type: 'ok',    label: 'ORDER PLACED' },
  NO_TRADE:            { type: 'muted', label: 'NO TRADE'     },
  SKIPPED_LOW_CONF:    { type: 'warn',  label: 'LOW CONF'     },
  SKIPPED_OPEN_TRADE:  { type: 'warn',  label: 'OPEN TRADE'   },
  ERROR_MARKET:        { type: 'block', label: 'MKT ERROR'    },
  ERROR_AI:            { type: 'block', label: 'AI ERROR'     },
  ERROR_ORDER:         { type: 'block', label: 'ORDER ERROR'  },
}

const SIG_C = {
  BUY:        'var(--green-hi)',
  SELL:       'var(--red-hi)',
  'NO TRADE': 'var(--t2)',
}

function RunRow({ run }) {
  const tag = ACTION_TAG[run.action] || { type: 'muted', label: run.action }
  const d   = new Date(run.started_at)
  return (
    <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--card)', border: '1px solid var(--b0)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', animation: 'fadeUp .3s ease' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 11, fontWeight: 800, color: SIG_C[run.signal] || 'var(--t2)', fontFamily: 'var(--mono)', minWidth: 80 }}>{run.signal}</span>
        <div>
          <div style={{ fontSize: 9, color: 'var(--t1)', fontFamily: 'var(--mono)' }}>{run.message?.slice(0, 60)}…</div>
          <div style={{ fontSize: 8, color: 'var(--t2)' }}>{d.toLocaleTimeString()} · {run.confidence}% · {run.filters}/9</div>
        </div>
      </div>
      <Tag type={tag.type}>{tag.label}</Tag>
    </div>
  )
}

export default function BotPanel() {
  const [status,   setStatus]   = useState(null)
  const [history,  setHistory]  = useState([])
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)
  const [config,   setConfig]   = useState({
    account_balance:    10000,
    min_confidence:     70,
    min_filters:        7,
    scan_interval_secs: 300,
    allow_one_trade:    true,
  })

  const refresh = useCallback(async () => {
    try {
      const [s, h] = await Promise.all([
        api('/api/bot/status'),
        api('/api/bot/history'),
      ])
      setStatus(s)
      setHistory(h)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    refresh()
    const t = setInterval(refresh, 10000)  // refresh every 10s
    return () => clearInterval(t)
  }, [refresh])

  async function handleStart() {
    setLoading(true)
    try {
      await api('/api/bot/start', 'POST', {
        account_balance:    config.account_balance,
        min_confidence:     config.min_confidence,
        min_filters:        config.min_filters,
        scan_interval_secs: config.scan_interval_secs,
        allow_one_trade:    config.allow_one_trade,
        enabled:            true,
      })
      await refresh()
    } catch (e) { setError(e.message) }
    setLoading(false)
  }

  async function handleStop() {
    setLoading(true)
    try {
      await api('/api/bot/stop', 'POST')
      await refresh()
    } catch (e) { setError(e.message) }
    setLoading(false)
  }

  async function handleRunOnce() {
    setLoading(true)
    try {
      await api('/api/bot/run-once', 'POST')
      await refresh()
    } catch (e) { setError(e.message) }
    setLoading(false)
  }

  async function handleCloseTrade() {
    if (!confirm('Close the open trade on OANDA immediately?')) return
    setLoading(true)
    try {
      await api('/api/bot/close-trade', 'POST')
      await refresh()
    } catch (e) { setError(e.message) }
    setLoading(false)
  }

  const running    = status?.running || false
  const openTrade  = status?.open_trade || null

  const IS = { background:'var(--input)', border:'1px solid var(--b1)', borderRadius:6, padding:'6px 10px', color:'var(--t0)', fontSize:12, fontFamily:'var(--mono)', outline:'none', width:'100%', boxSizing:'border-box' }

  return (
    <div>

      {/* ── Status banner ── */}
      <div style={{ padding:'14px 18px', borderRadius:10, marginBottom:14, border:`1px solid ${running ? 'rgba(16,185,129,.35)' : 'var(--b1)'}`, background: running ? 'rgba(16,185,129,.06)' : 'var(--panel)', display:'flex', alignItems:'center', justifyContent:'space-between' }}>
        <div>
          <div style={{ fontSize:9, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:2, marginBottom:4 }}>BOT STATUS</div>
          <div style={{ display:'flex', alignItems:'center', gap:10 }}>
            <div style={{ width:10, height:10, borderRadius:'50%', background: running ? 'var(--green)' : 'var(--t3)', boxShadow: running ? '0 0 10px var(--green)' : 'none', animation: running ? 'pulse 1.5s infinite' : 'none' }} />
            <span style={{ fontSize:16, fontWeight:800, color: running ? 'var(--green-hi)' : 'var(--t2)', fontFamily:'var(--mono)' }}>
              {running ? 'RUNNING' : 'STOPPED'}
            </span>
          </div>
          {status?.started_at && running && (
            <div style={{ fontSize:9, color:'var(--t2)', fontFamily:'var(--mono)', marginTop:4 }}>
              Started: {new Date(status.started_at).toLocaleTimeString()}
            </div>
          )}
        </div>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:10 }}>
          <StatBox label="Total Runs"   value={status?.total_runs    ?? 0} color="var(--cyan)"      />
          <StatBox label="Trades Placed" value={status?.trades_placed ?? 0} color="var(--green-hi)" />
          <StatBox label="Open Trade"    value={openTrade ? 'YES' : 'NO'}   color={openTrade ? 'var(--amber)' : 'var(--t2)'} />
        </div>
      </div>

      {/* ── Open trade card ── */}
      {openTrade && (
        <Panel style={{ marginBottom:14, border:'1px solid rgba(245,158,11,.3)', background:'rgba(245,158,11,.04)' }}>
          <SectionLabel>◈ OPEN TRADE — EUR/CHF</SectionLabel>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:10, marginBottom:12 }}>
            {[
              { l:'SIDE',   v:openTrade.side,               c: openTrade.side==='BUY'?'var(--green-hi)':'var(--red-hi)' },
              { l:'ENTRY',  v:openTrade.entry_price?.toFixed(5),  c:'var(--cyan)'     },
              { l:'STOP',   v:openTrade.stop_loss?.toFixed(5),    c:'var(--red-hi)'   },
              { l:'TP1',    v:openTrade.take_profit_1?.toFixed(5),c:'var(--green-hi)' },
              { l:'LOTS',   v:openTrade.position_size_lots,       c:'var(--t0)'       },
              { l:'RISK %', v:`${openTrade.risk_percent}%`,       c:'var(--amber)'    },
              { l:'$ RISK', v:`$${openTrade.risk_amount_usd?.toFixed(2)}`, c:'var(--amber)' },
              { l:'TRADE ID',v:openTrade.oanda_trade_id,          c:'var(--t2)'       },
            ].map(({l,v,c}) => (
              <div key={l} style={{ background:'rgba(255,255,255,.03)', borderRadius:7, padding:'9px 8px', textAlign:'center' }}>
                <div style={{ fontSize:7, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:1, marginBottom:4 }}>{l}</div>
                <div style={{ fontSize:12, fontWeight:700, color:c, fontFamily:'var(--mono)' }}>{v??'—'}</div>
              </div>
            ))}
          </div>
          <button onClick={handleCloseTrade} disabled={loading} style={{ width:'100%', padding:'9px', borderRadius:8, border:'1px solid rgba(239,68,68,.4)', background:'rgba(239,68,68,.08)', color:'var(--red-hi)', fontSize:11, fontFamily:'var(--mono)', fontWeight:700, cursor:'pointer', letterSpacing:1 }}>
            🚨 EMERGENCY CLOSE TRADE
          </button>
        </Panel>
      )}

      {/* ── Config ── */}
      <Panel style={{ marginBottom:14 }}>
        <SectionLabel>◈ BOT CONFIGURATION</SectionLabel>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
          {[
            { l:'Account Balance ($)', k:'account_balance', type:'number' },
            { l:'Scan Interval (sec)', k:'scan_interval_secs', type:'number' },
            { l:'Min Confidence (%)',  k:'min_confidence',  type:'number' },
            { l:'Min Filters (/ 9)',   k:'min_filters',     type:'number' },
          ].map(({ l, k, type }) => (
            <div key={k}>
              <div style={{ fontSize:9, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:1, marginBottom:5 }}>{l}</div>
              <input type={type} value={config[k]} disabled={running}
                onChange={e => setConfig(p => ({ ...p, [k]: Number(e.target.value) }))}
                style={{ ...IS, opacity: running ? 0.5 : 1 }} />
            </div>
          ))}
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:10, marginTop:12 }}>
          <input type="checkbox" id="one_trade" checked={config.allow_one_trade} disabled={running}
            onChange={e => setConfig(p => ({ ...p, allow_one_trade: e.target.checked }))} />
          <label htmlFor="one_trade" style={{ fontSize:10, color:'var(--t1)', fontFamily:'var(--mono)' }}>
            One trade at a time (skip if position already open)
          </label>
        </div>
        {running && <div style={{ fontSize:9, color:'var(--amber)', fontFamily:'var(--mono)', marginTop:8 }}>⚠ Stop the bot to change configuration.</div>}
      </Panel>

      {/* ── Controls ── */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:10, marginBottom:14 }}>
        <button onClick={handleStart} disabled={running || loading} style={{ padding:'12px', borderRadius:9, border:'none', background: running||loading ? 'var(--card)' : 'linear-gradient(135deg,#065f46,#10b981)', color: running||loading ? 'var(--t2)' : '#fff', fontSize:11, fontFamily:'var(--mono)', fontWeight:700, cursor: running||loading ? 'not-allowed' : 'pointer', letterSpacing:1, transition:'all .2s' }}>
          ▶ START BOT
        </button>
        <button onClick={handleStop} disabled={!running || loading} style={{ padding:'12px', borderRadius:9, border:'none', background: !running||loading ? 'var(--card)' : 'rgba(239,68,68,.15)', color: !running||loading ? 'var(--t2)' : 'var(--red-hi)', fontSize:11, fontFamily:'var(--mono)', fontWeight:700, cursor: !running||loading ? 'not-allowed' : 'pointer', border:`1px solid ${!running ? 'transparent' : 'rgba(239,68,68,.3)'}`, letterSpacing:1, transition:'all .2s' }}>
          ■ STOP BOT
        </button>
        <button onClick={handleRunOnce} disabled={loading} style={{ padding:'12px', borderRadius:9, border:'1px solid var(--b2)', background:'transparent', color:'var(--cyan)', fontSize:11, fontFamily:'var(--mono)', fontWeight:700, cursor: loading ? 'not-allowed' : 'pointer', letterSpacing:1 }}>
          ↻ RUN ONCE
        </button>
      </div>

      {error && <Alert type="block" style={{ marginBottom:14 }}>⚠ {error}</Alert>}

      {/* ── Run history ── */}
      <Panel>
        <SectionLabel>◈ BOT RUN HISTORY</SectionLabel>
        {history.length === 0 ? (
          <div style={{ textAlign:'center', padding:'30px 0', color:'var(--t3)', fontFamily:'var(--mono)', fontSize:11 }}>No runs yet — start the bot or click Run Once.</div>
        ) : (
          <div style={{ display:'flex', flexDirection:'column', gap:7 }}>
            {history.slice(0, 20).map(r => <RunRow key={r.run_id} run={r} />)}
          </div>
        )}
      </Panel>
    </div>
  )
}
