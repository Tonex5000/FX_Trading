import { Badge } from './UI'

const THEME = {
  'BUY':      { bg:'#061410', border:'#10b981', text:'#34d399', glow:'rgba(16,185,129,.12)', label:'LONG'  },
  'SELL':     { bg:'#140608', border:'#ef4444', text:'#f87171', glow:'rgba(239,68,68,.12)',  label:'SHORT' },
  'NO TRADE': { bg:'#08101e', border:'#1a3a5c', text:'#4a6a88', glow:'rgba(0,0,0,0)',        label:'WAIT'  },
}
const REGIME_C = { TRENDING:'var(--green-hi)', BORDERLINE:'var(--amber)', CHOPPY:'var(--red-hi)' }
const CL = { tf_4h_1h_agree:'4H+1H Agree', ema21_aligned:'EMA 21', adx_regime_valid:'ADX Regime', pullback_entry:'Pullback', session_valid:'Session', news_window_clear:'News Clear', snb_risk_clear:'SNB Clear', stop_within_atr15:'Stop≤ATR×1.5', rr_minimum_1to2:'R:R≥1:2' }

function Arc({ value, color }) {
  const r=30,cx=36,cy=36, c=2*Math.PI*r, d=c*(value/100)
  return (
    <div style={{ textAlign:'center' }}>
      <svg width="72" height="72">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--b0)" strokeWidth="4"/>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth="4" strokeDasharray={`${d} ${c-d}`} strokeLinecap="round" transform={`rotate(-90 ${cx} ${cy})`} style={{ transition:'stroke-dasharray .5s' }}/>
        <text x={cx} y={cy+1} textAnchor="middle" dominantBaseline="middle" fill={color} fontSize="13" fontWeight="800" fontFamily="var(--mono)">{value}</text>
      </svg>
      <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:1, marginTop:-2 }}>CONFIDENCE</div>
    </div>
  )
}

function FilterBar({ passed }) {
  return (
    <div style={{ display:'flex', gap:3, alignItems:'center' }}>
      {Array.from({length:9}).map((_,i) => <div key={i} style={{ height:3, flex:1, borderRadius:3, background:i<passed?'var(--green)':'var(--b1)', transition:'background .3s' }}/>)}
      <span style={{ fontSize:9, color:'var(--t2)', fontFamily:'var(--mono)', marginLeft:4 }}>{passed}/9</span>
    </div>
  )
}

export default function SignalResult({ signal, balance }) {
  if (!signal) return null
  const T = THEME[signal.signal] || THEME['NO TRADE']
  const risk$ = signal.risk_percent ? balance * signal.risk_percent / 100 : null

  return (
    <div style={{ borderRadius:'var(--r-xl)', border:`1px solid ${T.border}`, background:T.bg, boxShadow:`0 8px 40px ${T.glow}`, overflow:'hidden', animation:'fadeUp .4s ease', marginTop:16 }}>

      {/* Header */}
      <div style={{ padding:'20px 24px', borderBottom:`1px solid ${T.border}22`, background:T.glow, display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
        <div>
          <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:2, marginBottom:4 }}>AI DECISION</div>
          <div style={{ fontSize:44, fontWeight:900, color:T.text, fontFamily:'var(--mono)', letterSpacing:3, lineHeight:1 }}>{signal.signal}</div>
          <div style={{ display:'flex', gap:7, marginTop:8, flexWrap:'wrap' }}>
            <Badge color={T.border}>{T.label}</Badge>
            {signal.regime && <Badge color={REGIME_C[signal.regime]}>{signal.regime}</Badge>}
            {signal.market_condition && <Badge color="var(--t2)">{signal.market_condition.replace(/_/g,' ')}</Badge>}
          </div>
          {signal.blocked_by && <div style={{ fontSize:10, color:'var(--red-hi)', fontFamily:'var(--mono)', marginTop:8 }}>Blocked: {signal.blocked_by}</div>}
          <div style={{ marginTop:12, maxWidth:260 }}><FilterBar passed={signal.filters_passed||0}/></div>
        </div>
        <Arc value={signal.confidence} color={T.text}/>
      </div>

      {/* Trade levels */}
      {signal.signal !== 'NO TRADE' && signal.entry_price && (
        <div style={{ padding:'16px 24px', borderBottom:`1px solid ${T.border}18` }}>
          <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:2, marginBottom:10 }}>TRADE LEVELS</div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:8 }}>
            {[
              { l:'ENTRY', v:signal.entry_price?.toFixed(5), sub:signal.entry_type||'',         c:'var(--cyan)'      },
              { l:'STOP',  v:signal.stop_loss?.toFixed(5),   sub:`${signal.stop_pips||'?'}p`,   c:'var(--red-hi)'    },
              { l:'TP1',   v:signal.take_profit_1?.toFixed(5),sub:`${signal.tp1_pips||'?'}p`,   c:'var(--green-hi)'  },
              { l:'TP2',   v:signal.take_profit_2?.toFixed(5),sub:'partial',                    c:'var(--green)'     },
              { l:'R:R',   v:signal.risk_reward,              sub:signal.stop_basis||'',         c:'var(--amber-hi)'  },
            ].map(({l,v,sub,c}) => (
              <div key={l} style={{ background:'rgba(255,255,255,.03)', borderRadius:7, padding:'9px 7px', textAlign:'center' }}>
                <div style={{ fontSize:7, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:1, marginBottom:4 }}>{l}</div>
                <div style={{ fontSize:13, fontWeight:800, color:v?c:'var(--t3)', fontFamily:'var(--mono)' }}>{v||'—'}</div>
                {sub && <div style={{ fontSize:7, color:'var(--t3)', fontFamily:'var(--mono)', marginTop:3 }}>{sub}</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Position size */}
      {signal.signal !== 'NO TRADE' && signal.risk_percent && (
        <div style={{ padding:'14px 24px', borderBottom:`1px solid ${T.border}18`, background:'rgba(245,158,11,.04)' }}>
          <div style={{ fontSize:8, color:'var(--amber)', fontFamily:'var(--mono)', letterSpacing:2, marginBottom:8 }}>POSITION SIZE</div>
          <div style={{ display:'flex', gap:22, flexWrap:'wrap' }}>
            {[
              { l:'Risk %', v:`${signal.risk_percent}%`,            c:'var(--amber-hi)' },
              { l:'$ Risk', v:risk$?`$${risk$.toFixed(2)}`:'—',     c:'var(--amber-hi)' },
              { l:'Target', v:risk$?`$${(risk$*2).toFixed(2)}`:'—', c:'var(--green-hi)' },
              { l:'Lots',   v:signal.position_size_lots??'—',        c:'var(--cyan)'     },
              { l:'Sized',  v:signal.risk_percent===1.0?'Full ✓':'Half ⚠', c:'var(--t1)' },
            ].map(({l,v,c}) => (
              <div key={l}><span style={{ fontSize:9, color:'var(--t2)', fontFamily:'var(--mono)' }}>{l}: </span><span style={{ fontSize:10, fontWeight:700, color:c, fontFamily:'var(--mono)' }}>{v}</span></div>
            ))}
          </div>
        </div>
      )}

      {/* Confluence */}
      {signal.confluence_check && (
        <div style={{ padding:'14px 24px', borderBottom:`1px solid ${T.border}18` }}>
          <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:2, marginBottom:9 }}>9-POINT CONFLUENCE</div>
          <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
            {Object.entries(signal.confluence_check).map(([k,v]) => (
              <span key={k} style={{ padding:'3px 9px', borderRadius:20, fontSize:9, fontWeight:600, fontFamily:'var(--mono)', background:v?'rgba(16,185,129,.10)':'rgba(239,68,68,.10)', color:v?'var(--green-hi)':'var(--red-hi)', border:`1px solid ${v?'rgba(16,185,129,.3)':'rgba(239,68,68,.3)'}` }}>
                {v?'✓':'✗'} {CL[k]||k}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Text sections */}
      {[
        { l:'AI REASONING',    v:signal.reasoning,       c:'var(--t1)'         },
        { l:'NEWS ASSESSMENT', v:signal.news_assessment, c:'var(--t1)'         },
        { l:signal.signal!=='NO TRADE'?'EXECUTION PLAN':'WHAT TO WATCH', v:signal.trade_plan, c:'var(--cyan-dim)' },
        { l:'MARKET CONTEXT',  v:signal.market_context,  c:'var(--t1)'         },
        { l:'NEXT CHECK',      v:signal.next_check,      c:'var(--amber)'      },
      ].filter(s=>s.v).map(({l,v,c})=>(
        <div key={l} style={{ padding:'12px 24px', borderBottom:`1px solid ${T.border}18` }}>
          <div style={{ fontSize:8, color:'var(--t3)', fontFamily:'var(--mono)', letterSpacing:2, marginBottom:5 }}>{l}</div>
          <div style={{ fontSize:11, color:c, lineHeight:1.8, fontFamily:'var(--sans)' }}>{v}</div>
        </div>
      ))}

      {signal.warnings?.length > 0 && (
        <div style={{ padding:'12px 24px' }}>
          {signal.warnings.map((w,i) => <div key={i} style={{ fontSize:10, color:'var(--amber-hi)', fontFamily:'var(--mono)', marginBottom:4 }}>⚠ {w}</div>)}
        </div>
      )}
    </div>
  )
}
