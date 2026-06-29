import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { StatBox, Panel, SectionLabel } from './UI'

const SC = { BUY:{t:'var(--green-hi)',bg:'#06141010',b:'#10b98122'}, SELL:{t:'var(--red-hi)',bg:'#14060810',b:'#ef444422'}, 'NO TRADE':{t:'var(--t2)',bg:'#08101e10',b:'#1a3a5c22'} }

function Row({ entry, onUpdate }) {
  const [open, setOpen] = useState(false)
  const [edit, setEdit] = useState(false)
  const [oc,   setOc]   = useState(entry.outcome||'')
  const [pnl,  setPnl]  = useState(entry.pnl??'')
  const [note, setNote] = useState(entry.notes||'')
  const C = SC[entry.signal]||SC['NO TRADE']
  const d = new Date(entry.ts)
  const outcomeC = entry.outcome==='WIN'?'var(--green-hi)':entry.outcome==='LOSS'?'var(--red-hi)':'var(--t2)'
  const IS = { background:'var(--deep)', border:'1px solid var(--b1)', borderRadius:5, padding:'5px 7px', color:'var(--t0)', fontSize:10, fontFamily:'var(--mono)', outline:'none', width:'100%', boxSizing:'border-box' }

  return (
    <div style={{ borderRadius:8, border:`1px solid ${C.b}`, background:C.bg, overflow:'hidden' }}>
      <div onClick={()=>setOpen(o=>!o)} style={{ padding:'10px 14px', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'space-between' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <span style={{ fontSize:11, fontWeight:800, color:C.t, fontFamily:'var(--mono)', minWidth:76 }}>{entry.signal}</span>
          <div>
            <div style={{ fontSize:9, color:'var(--t1)', fontFamily:'var(--mono)' }}>{entry.session?.replace(/_/g,' ').toUpperCase()} · {entry.trend_4h?.replace(/_/g,' ')}</div>
            <div style={{ fontSize:8, color:'var(--t2)' }}>{d.toLocaleDateString()} {d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</div>
          </div>
        </div>
        <div style={{ display:'flex', gap:10, alignItems:'center' }}>
          <div style={{ textAlign:'right' }}>
            <div style={{ fontSize:11, color:'var(--cyan)', fontWeight:700, fontFamily:'var(--mono)' }}>{entry.price?.toFixed(5)}</div>
            <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)' }}>ADX {entry.adx} · {entry.filters}/9 · {entry.confidence}%</div>
          </div>
          {entry.outcome && <div style={{ textAlign:'center' }}><div style={{ fontSize:10, fontWeight:800, color:outcomeC, fontFamily:'var(--mono)' }}>{entry.outcome}</div>{entry.pnl!=null&&<div style={{ fontSize:9, color:outcomeC }}>{entry.pnl>=0?'+':''}${entry.pnl}</div>}</div>}
          <span style={{ color:'var(--t2)', fontSize:9 }}>{open?'▲':'▼'}</span>
        </div>
      </div>
      {open && (
        <div style={{ padding:'0 14px 12px', borderTop:`1px solid ${C.b}` }}>
          <div style={{ paddingTop:10, display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:7, marginBottom:8 }}>
            {[{l:'Regime',v:entry.regime},{l:'News',v:entry.news_risk},{l:'R:R',v:entry.rr},{l:'Lots',v:entry.lots}].map(({l,v})=>(
              <div key={l} style={{ background:'rgba(255,255,255,.03)', borderRadius:6, padding:8, textAlign:'center' }}>
                <div style={{ fontSize:7, color:'var(--t2)', fontFamily:'var(--mono)', marginBottom:3 }}>{l}</div>
                <div style={{ fontSize:10, fontWeight:700, fontFamily:'var(--mono)', color:'var(--t0)' }}>{v??'—'}</div>
              </div>
            ))}
          </div>
          {entry.blocked_by && <div style={{ fontSize:9, color:'var(--red-hi)', fontFamily:'var(--mono)', marginBottom:6 }}>Blocked: {entry.blocked_by}</div>}
          <button onClick={()=>setEdit(e=>!e)} style={{ fontSize:8, padding:'4px 10px', background:'transparent', border:'1px solid var(--b2)', borderRadius:5, color:'var(--t2)', cursor:'pointer', fontFamily:'var(--mono)' }}>{edit?'CANCEL':'+ LOG OUTCOME'}</button>
          {edit && (
            <div style={{ padding:'10px 12px', background:'var(--deep)', borderRadius:7, marginTop:8, border:'1px solid var(--b0)' }}>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:7, marginBottom:7 }}>
                <select value={oc} onChange={e=>setOc(e.target.value)} style={{ ...IS, appearance:'none' }}>
                  <option value="">Outcome…</option>
                  <option value="WIN">WIN</option><option value="LOSS">LOSS</option>
                  <option value="BREAKEVEN">BREAKEVEN</option><option value="NOT_TAKEN">Not Taken</option>
                </select>
                <input type="number" placeholder="P&L ($)" value={pnl} onChange={e=>setPnl(e.target.value)} style={IS}/>
              </div>
              <input type="text" placeholder="Notes…" value={note} onChange={e=>setNote(e.target.value)} style={{ ...IS, marginBottom:7 }}/>
              <button onClick={()=>{ onUpdate(entry.id,oc,pnl,note); setEdit(false) }} style={{ padding:'5px 14px', background:'var(--blue)', border:'none', borderRadius:5, color:'#fff', fontSize:9, fontFamily:'var(--mono)', fontWeight:700, cursor:'pointer' }}>SAVE</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function Journal({ entries, stats, onUpdate, onClear }) {
  const [filter, setFilter] = useState('ALL')
  const visible = entries.filter(e => filter==='ALL'?true:filter==='SIGNALS'?e.signal!=='NO TRADE':filter==='NO_TRADE'?e.signal==='NO TRADE':filter==='WINS'?e.outcome==='WIN':e.outcome==='LOSS')
  const curve = entries.filter(e=>e.pnl!=null).slice().reverse().reduce((a,e,i)=>[...a,{i:i+1,v:+((a[i-1]?.v||0)+e.pnl).toFixed(2)}],[])

  return (
    <div>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:9, marginBottom:10 }}>
        <StatBox label="Total"       value={stats.total}  color="var(--cyan)" />
        <StatBox label="Win Rate"    value={stats.winRate!=null?`${stats.winRate}%`:'—'} color={stats.winRate>=50?'var(--green-hi)':'var(--red-hi)'} />
        <StatBox label="P&L"         value={stats.pnl?`${stats.pnl>=0?'+':''}$${stats.pnl}`:'—'} color={stats.pnl>=0?'var(--green-hi)':'var(--red-hi)'} />
        <StatBox label="Prof. Factor" value={stats.pf??'—'} color={stats.pf>=1.5?'var(--green-hi)':'var(--amber)'} />
      </div>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:9, marginBottom:14 }}>
        <StatBox label="Signals"  value={stats.signals}  color="var(--green)"    />
        <StatBox label="No Trade" value={stats.noTrade}  color="var(--t2)"       />
        <StatBox label="Wins"     value={stats.wins}     color="var(--green-hi)" />
        <StatBox label="Losses"   value={stats.losses}   color="var(--red-hi)"   />
      </div>

      {curve.length >= 2 && (
        <Panel style={{ marginBottom:14 }}>
          <SectionLabel>◈ EQUITY CURVE</SectionLabel>
          <ResponsiveContainer width="100%" height={90}>
            <LineChart data={curve}>
              <XAxis dataKey="i" hide/><YAxis hide/>
              <Tooltip contentStyle={{ background:'var(--card)', border:'1px solid var(--b1)', borderRadius:7, fontSize:10, fontFamily:'var(--mono)' }} formatter={v=>[`${v>=0?'+':''}$${v}`,'P&L']}/>
              <ReferenceLine y={0} stroke="var(--b1)" strokeDasharray="3 3"/>
              <Line type="monotone" dataKey="v" stroke="var(--cyan)" strokeWidth={2} dot={false}/>
            </LineChart>
          </ResponsiveContainer>
        </Panel>
      )}

      <div style={{ display:'flex', gap:3, marginBottom:12, background:'var(--panel)', borderRadius:9, padding:3 }}>
        {[['ALL','All'],['SIGNALS','Signals'],['NO_TRADE','No Trade'],['WINS','Wins'],['LOSSES','Losses']].map(([v,l])=>(
          <button key={v} onClick={()=>setFilter(v)} style={{ flex:1, padding:'6px 0', borderRadius:7, border:'none', cursor:'pointer', background:filter===v?'var(--blue)':'transparent', color:filter===v?'#fff':'var(--t2)', fontSize:9, fontFamily:'var(--mono)', fontWeight:700, letterSpacing:1, transition:'all .2s' }}>{l}</button>
        ))}
      </div>

      {visible.length===0 ? (
        <div style={{ textAlign:'center', padding:'48px 0', color:'var(--t3)', fontFamily:'var(--mono)', fontSize:11 }}>
          <div style={{ fontSize:32, marginBottom:8 }}>◷</div>No entries yet.
        </div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:7 }}>
          {visible.map(e=><Row key={e.id} entry={e} onUpdate={onUpdate}/>)}
        </div>
      )}

      {entries.length>0 && <div style={{ textAlign:'center', marginTop:18 }}><button onClick={onClear} style={{ padding:'5px 16px', background:'transparent', border:'1px solid rgba(239,68,68,.25)', borderRadius:6, color:'rgba(248,113,113,.5)', cursor:'pointer', fontSize:8, fontFamily:'var(--mono)' }}>CLEAR ALL</button></div>}
    </div>
  )
}
