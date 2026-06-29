export function Spinner({ size = 14, color = 'var(--cyan)' }) {
  return <span style={{ display:'inline-block', width:size, height:size, border:`2px solid var(--b1)`, borderTopColor:color, borderRadius:'50%', animation:'spin 0.7s linear infinite', flexShrink:0 }} />
}

export function Badge({ children, color='var(--cyan)', style={} }) {
  return <span style={{ padding:'2px 9px', borderRadius:20, fontSize:9, fontWeight:700, fontFamily:'var(--mono)', letterSpacing:1, color, background:`${color}18`, border:`1px solid ${color}40`, ...style }}>{children}</span>
}

export function Tag({ children, type='info' }) {
  const m = { ok:{c:'var(--green)',b:'var(--green)'}, warn:{c:'var(--amber)',b:'var(--amber)'}, block:{c:'var(--red)',b:'var(--red)'}, info:{c:'var(--cyan)',b:'var(--cyan)'}, muted:{c:'var(--t2)',b:'var(--b2)'} }
  const {c,b} = m[type]||m.info
  return <span style={{ padding:'2px 8px', borderRadius:4, fontSize:9, fontWeight:700, fontFamily:'var(--mono)', letterSpacing:1, color:c, background:`${b}18`, border:`1px solid ${b}33` }}>{children}</span>
}

export function Alert({ type='warn', children, style={} }) {
  const m = { ok:{bg:'#10b98112',border:'#10b98144',c:'var(--green-hi)'}, warn:{bg:'#f59e0b12',border:'#f59e0b44',c:'var(--amber-hi)'}, block:{bg:'#ef444412',border:'#ef444444',c:'var(--red-hi)'}, info:{bg:'#22d3ee10',border:'#22d3ee40',c:'var(--cyan)'} }
  const s = m[type]||m.warn
  return <div style={{ padding:'9px 13px', borderRadius:7, marginTop:10, background:s.bg, border:`1px solid ${s.border}`, color:s.c, fontSize:10, fontFamily:'var(--mono)', lineHeight:1.65, ...style }}>{children}</div>
}

export function StatBox({ label, value, color='var(--cyan)', sub }) {
  return (
    <div style={{ background:'var(--card)', border:'1px solid var(--b0)', borderRadius:9, padding:'14px 16px', textAlign:'center' }}>
      <div style={{ fontSize:22, fontWeight:900, color, fontFamily:'var(--mono)', lineHeight:1 }}>{value??'—'}</div>
      <div style={{ fontSize:9, color:'var(--t2)', letterSpacing:1, marginTop:5, fontFamily:'var(--mono)' }}>{label}</div>
      {sub && <div style={{ fontSize:9, color:'var(--t3)', marginTop:2 }}>{sub}</div>}
    </div>
  )
}

export function DataRow({ label, value, color='var(--t0)' }) {
  return (
    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'5px 0', borderBottom:'1px solid var(--b0)' }}>
      <span style={{ fontSize:10, color:'var(--t2)', fontFamily:'var(--mono)' }}>{label}</span>
      <span style={{ fontSize:11, fontWeight:600, color, fontFamily:'var(--mono)' }}>{value??'—'}</span>
    </div>
  )
}

export function SectionLabel({ children }) {
  return <div style={{ fontSize:9, color:'var(--cyan-dim)', letterSpacing:2, fontFamily:'var(--mono)', fontWeight:700, marginBottom:12, paddingBottom:7, borderBottom:'1px solid var(--b0)', textTransform:'uppercase' }}>{children}</div>
}

export function Panel({ children, style={} }) {
  return <div style={{ background:'var(--panel)', border:'1px solid var(--b0)', borderRadius:'var(--r-lg)', padding:'16px 18px', ...style }}>{children}</div>
}
