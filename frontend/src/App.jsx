import { useState } from 'react'
import Header          from './components/Header'
import MarketSnapshot  from './components/MarketSnapshot'
import NewsPanel       from './components/NewsPanel'
import SignalResult    from './components/SignalResult'
import Journal         from './components/Journal'
import BotPanel        from './components/BotPanel'
import { Spinner }     from './components/UI'
import { useAnalysis, STEP } from './hooks/useAnalysis'
import { useJournal }        from './hooks/useJournal'

const TABS = [
  { id: 'signal',  label: '⟁  Signal Engine' },
  { id: 'bot',     label: '🤖  Trading Bot'   },
  { id: 'journal', label: '◷  Journal'        },
]

const STEP_LABEL = {
  [STEP.FETCHING]:  'Step 1/2 — Fetching OANDA price + ForexFactory news…',
  [STEP.ANALYZING]: 'Step 2/2 — Claude AI applying 7 filters…',
}

export default function App() {
  const [tab,     setTab]     = useState('signal')
  const [balance, setBalance] = useState(10000)

  const { run, step, isLoading, market, news, signal, error, lastRun } = useAnalysis()
  const { entries, add, update, clear, stats } = useJournal()

  async function handleAnalyze() {
    const result = await run(balance)
    if (result) add(result)
  }

  return (
    <div style={{ minHeight: '100vh' }}>
      <Header price={market?.price?.mid} step={step} lastRun={lastRun} />

      <main style={{ maxWidth: 920, margin: '0 auto', padding: '20px 16px 60px' }}>

        {/* ── TABS ── */}
        <div style={{ display:'flex', gap:3, marginBottom:18, background:'var(--panel)', borderRadius:11, padding:4, border:'1px solid var(--b0)' }}>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{ flex:1, padding:'8px 0', borderRadius:8, border:'none', cursor:'pointer', background:tab===t.id?'var(--blue)':'transparent', color:tab===t.id?'#fff':'var(--t2)', fontSize:11, fontFamily:'var(--mono)', fontWeight:700, letterSpacing:1, textTransform:'uppercase', transition:'all .2s', boxShadow:tab===t.id?'0 2px 10px rgba(18,84,168,.35)':'none' }}>
              {t.label}
            </button>
          ))}
        </div>

        {tab === 'signal' && (
          <>
            {/* Account Balance */}
            <div style={{ background:'var(--panel)', border:'1px solid var(--b0)', borderRadius:'var(--r-lg)', padding:'14px 18px', marginBottom:12, display:'flex', alignItems:'center', justifyContent:'space-between' }}>
              <div>
                <div style={{ fontSize:9, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:2, marginBottom:6 }}>ACCOUNT BALANCE ($)</div>
                <input
                  type="number" value={balance}
                  onChange={e => setBalance(Number(e.target.value))}
                  style={{ background:'var(--input)', border:'1px solid var(--b1)', borderRadius:6, padding:'7px 12px', color:'var(--t0)', fontSize:14, fontFamily:'var(--mono)', fontWeight:700, outline:'none', width:160 }}
                />
              </div>
              <div style={{ textAlign:'right' }}>
                <div style={{ fontSize:9, color:'var(--t2)', fontFamily:'var(--mono)', marginBottom:3 }}>Risk range</div>
                <div style={{ fontSize:12, color:'var(--amber)', fontFamily:'var(--mono)', fontWeight:700 }}>${(balance*0.005).toFixed(0)} – ${(balance*0.01).toFixed(0)}</div>
                <div style={{ fontSize:9, color:'var(--t3)', fontFamily:'var(--mono)', marginTop:2 }}>0.5% – 1.0%</div>
              </div>
            </div>

            {/* Analyze button */}
            <button
              onClick={handleAnalyze}
              disabled={isLoading}
              style={{ width:'100%', padding:'15px', borderRadius:12, border:'none', background:isLoading?'var(--card)':'linear-gradient(135deg,#1254a8,#0891b2)', color:isLoading?'var(--t2)':'#fff', fontSize:13, fontFamily:'var(--mono)', fontWeight:700, letterSpacing:2, cursor:isLoading?'not-allowed':'pointer', boxShadow:isLoading?'none':'0 4px 24px rgba(18,84,168,.35)', transition:'all .25s', display:'flex', alignItems:'center', justifyContent:'center', gap:10, marginBottom:16 }}
            >
              {isLoading ? (
                <><Spinner /> {STEP_LABEL[step] || 'Working…'}</>
              ) : (
                '⟁  ANALYZE — OANDA + NEWS + AI'
              )}
            </button>

            {error && (
              <div style={{ padding:'12px 16px', borderRadius:10, marginBottom:14, background:'rgba(239,68,68,.10)', border:'1px solid rgba(239,68,68,.30)', color:'var(--red-hi)', fontSize:11, fontFamily:'var(--mono)', lineHeight:1.7 }}>
                ⚠ {error}
                <div style={{ marginTop:6, fontSize:9, color:'var(--t2)' }}>
                  Check that your backend is running on {import.meta.env.VITE_API_URL || 'http://localhost:8000'} and your .env keys are set.
                </div>
              </div>
            )}

            {/* Auto-fetched data panels */}
            <MarketSnapshot market={market} news={news} />
            <NewsPanel news={news} />

            {/* AI signal result */}
            {signal && <SignalResult signal={signal} balance={balance} />}
          </>
        )}

        {tab === 'bot' && <BotPanel />}

        {tab === 'journal' && (
          <Journal entries={entries} stats={stats} onUpdate={update} onClear={clear} />
        )}

        <footer style={{ textAlign:'center', marginTop:40, paddingTop:20, borderTop:'1px solid var(--b0)', fontSize:9, color:'var(--t3)', fontFamily:'var(--mono)', letterSpacing:1, lineHeight:2 }}>
          EDUCATIONAL USE ONLY · NOT FINANCIAL ADVICE<br/>
          TEST ON OANDA PRACTICE ACCOUNT BEFORE LIVE TRADING<br/>
          BACKEND: FASTAPI · FRONTEND: REACT + VITE · AI: GROQ (QWEN3-32B)
        </footer>
      </main>
    </div>
  )
}
