import { STEP } from '../hooks/useAnalysis'

const INFO = {
  [STEP.IDLE]:      { dot:'#4a6a88', text:'Ready — click Analyze'        },
  [STEP.FETCHING]:  { dot:'#f59e0b', text:'Fetching OANDA + news data…'  },
  [STEP.ANALYZING]: { dot:'#22d3ee', text:'Claude AI analyzing…'         },
  [STEP.DONE]:      { dot:'#10b981', text:'Analysis complete'             },
  [STEP.ERROR]:     { dot:'#ef4444', text:'Error — see details below'     },
}

export default function Header({ price, step, lastRun }) {
  const info   = INFO[step] || INFO[STEP.IDLE]
  const isLive = step === STEP.FETCHING || step === STEP.ANALYZING

  return (
    <header style={{ height:56, padding:'0 24px', display:'flex', alignItems:'center', justifyContent:'space-between', borderBottom:'1px solid var(--b0)', background:'rgba(2,4,10,.96)', backdropFilter:'blur(16px)', position:'sticky', top:0, zIndex:200 }}>
      {/* Logo */}
      <div style={{ display:'flex', alignItems:'center', gap:10 }}>
        <div style={{ width:32, height:32, borderRadius:7, background:'linear-gradient(135deg,#1254a8,#0891b2)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:15, boxShadow:'0 2px 14px rgba(18,84,168,.45)' }}>⟁</div>
        <div>
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <span style={{ fontSize:13, fontWeight:800, color:'var(--t0)' }}>EUR/CHF AI</span>
            <span style={{ fontSize:8, background:'rgba(18,84,168,.3)', color:'var(--cyan)', padding:'2px 7px', borderRadius:10, fontFamily:'var(--mono)', letterSpacing:2 }}>AUTO v2</span>
          </div>
          <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:2, marginTop:1 }}>OANDA + FOREXFACTORY + CLAUDE AI</div>
        </div>
      </div>

      {/* Live price */}
      <div style={{ textAlign:'center' }}>
        <div style={{ fontSize:20, fontWeight:900, fontFamily:'var(--mono)', color:'var(--cyan)', letterSpacing:1 }}>{price ? price.toFixed(5) : '—.—————'}</div>
        <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:2 }}>EUR/CHF  LIVE</div>
      </div>

      {/* Status */}
      <div style={{ display:'flex', alignItems:'center', gap:8 }}>
        <div style={{ textAlign:'right' }}>
          <div style={{ fontSize:10, color:info.dot, fontFamily:'var(--mono)', fontWeight:600 }}>{info.text}</div>
          {lastRun && <div style={{ fontSize:8, color:'var(--t3)', fontFamily:'var(--mono)', marginTop:2 }}>Last: {lastRun.toLocaleTimeString()}</div>}
        </div>
        <div style={{ width:8, height:8, borderRadius:'50%', background:info.dot, boxShadow:`0 0 ${isLive?'12px':'5px'} ${info.dot}`, animation:isLive?'pulse 1s infinite':'none' }} />
      </div>
    </header>
  )
}
