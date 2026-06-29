import { Panel, SectionLabel, Tag } from './UI'

const IT = { High:'block', Medium:'warn', Low:'ok', Holiday:'muted' }
const minsLabel = m => m < 0 ? `${Math.abs(m)}m ago` : m < 60 ? `in ${m}m` : `in ${Math.floor(m/60)}h ${m%60}m`

export default function NewsPanel({ news }) {
  if (!news) return null
  const { events, risk, fetched_at } = news

  return (
    <Panel style={{ marginBottom:12 }}>
      <SectionLabel>◈ ECONOMIC CALENDAR — FOREXFACTORY LIVE</SectionLabel>

      <div style={{ padding:'10px 14px', borderRadius:8, marginBottom:12, background:'var(--card)', border:'1px solid var(--b0)', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <div>
          <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:2, marginBottom:3 }}>AGGREGATE RISK</div>
          <div style={{ fontSize:11, fontFamily:'var(--mono)', fontWeight:700, color:['snb_block','hard_block','window_block'].includes(risk?.level)?'var(--red-hi)':risk?.level==='caution'?'var(--amber-hi)':'var(--green)' }}>
            {risk?.label||'Loading…'}
          </div>
        </div>
        <div style={{ fontSize:8, color:'var(--t3)', fontFamily:'var(--mono)', textAlign:'right' }}>
          ForexFactory<br/>{fetched_at ? new Date(fetched_at).toLocaleTimeString() : ''}
        </div>
      </div>

      {events.length === 0 ? (
        <div style={{ textAlign:'center', padding:'14px 0', fontSize:10, color:'var(--t2)', fontFamily:'var(--mono)' }}>✓ No USD/CHF events in next 24h</div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
          {events.slice(0,10).map(ev => (
            <div key={ev.id} style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'8px 12px', borderRadius:7, background:ev.is_snb?'rgba(239,68,68,.08)':ev.is_high_impact?'rgba(239,68,68,.04)':'var(--card)', border:`1px solid ${ev.is_snb?'rgba(239,68,68,.3)':ev.is_high_impact?'rgba(239,68,68,.15)':'var(--b0)'}` }}>
              <div style={{ flex:1, minWidth:0 }}>
                <div style={{ display:'flex', alignItems:'center', gap:6, marginBottom:2 }}>
                  <span style={{ fontSize:8, fontFamily:'var(--mono)', fontWeight:700, color:ev.currency==='CHF'?'var(--red-hi)':'var(--cyan)', background:'var(--b0)', padding:'1px 5px', borderRadius:3 }}>{ev.currency}</span>
                  <span style={{ fontSize:10, color:'var(--t0)', fontFamily:'var(--mono)', fontWeight:600, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', maxWidth:180 }}>{ev.title}</span>
                  {ev.is_snb && <span style={{ fontSize:8, color:'var(--red-hi)', fontFamily:'var(--mono)', fontWeight:700 }}>⚠ SNB</span>}
                </div>
                <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)' }}>
                  {new Date(ev.event_time).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})} UTC
                  {ev.forecast ? `  · Forecast: ${ev.forecast}` : ''}
                </div>
              </div>
              <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-end', gap:3, marginLeft:10 }}>
                <Tag type={IT[ev.impact]||'muted'}>{ev.impact}</Tag>
                <span style={{ fontSize:9, fontFamily:'var(--mono)', fontWeight:700, color:Math.abs(ev.mins_away)<=30?'var(--red-hi)':ev.mins_away<=60?'var(--amber)':'var(--t2)' }}>{minsLabel(ev.mins_away)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Panel>
  )
}
