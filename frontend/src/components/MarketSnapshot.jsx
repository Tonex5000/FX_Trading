import { Panel, SectionLabel, DataRow, Tag, Alert } from './UI'

const T_LABEL = { strong_up:{l:'Strong Uptrend ↑↑',c:'var(--green-hi)'}, weak_up:{l:'Weak Uptrend ↑',c:'var(--green)'}, ranging:{l:'Ranging ↔',c:'var(--amber)'}, weak_down:{l:'Weak Downtrend ↓',c:'var(--red)'}, strong_down:{l:'Strong Downtrend ↓↓',c:'var(--red-hi)'} }
const V_COLOR = { very_low:'var(--green-hi)', low:'var(--green)', medium:'var(--amber)', high:'var(--red)', extreme:'var(--red-hi)' }
const adxC    = a => a >= 25 ? 'var(--green-hi)' : a >= 20 ? 'var(--amber)' : 'var(--red-hi)'

const isBull = t => ['strong_up','weak_up'].includes(t)
const isBear = t => ['strong_down','weak_down'].includes(t)
const align  = (a,b) => (isBull(a)&&isBull(b)) || (isBear(a)&&isBear(b))

export default function MarketSnapshot({ market, news }) {
  if (!market) return (
    <Panel style={{ marginBottom:12 }}>
      <SectionLabel>◈ AUTO-FETCHED MARKET DATA — OANDA</SectionLabel>
      <div style={{ textAlign:'center', padding:'24px 0', color:'var(--t2)', fontSize:11, fontFamily:'var(--mono)' }}>Run an analysis to load live data…</div>
    </Panel>
  )

  const { price, adx, adx_1h, atr, atr_1h, trend_4h, trend_1h, ema_4h, above_ema_4h, volatility, session } = market
  const t4 = T_LABEL[trend_4h]||{}, t1 = T_LABEL[trend_1h]||{}
  const aligned = align(trend_4h, trend_1h)

  return (
    <Panel style={{ marginBottom:12 }}>
      <SectionLabel>◈ AUTO-FETCHED MARKET DATA — OANDA LIVE</SectionLabel>

      {/* Price grid */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8, marginBottom:14 }}>
        {[
          { l:'MID',    v:price.mid.toFixed(5),                c:'var(--cyan)'  },
          { l:'BID',    v:price.bid.toFixed(5),                c:'var(--t1)'   },
          { l:'ASK',    v:price.ask.toFixed(5),                c:'var(--t1)'   },
          { l:'SPREAD', v:(price.spread*10000).toFixed(1)+'p', c: price.spread<0.0003?'var(--green)':'var(--amber)' },
        ].map(({ l, v, c }) => (
          <div key={l} style={{ background:'var(--card)', borderRadius:7, padding:10, textAlign:'center', border:'1px solid var(--b0)' }}>
            <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:1, marginBottom:4 }}>{l}</div>
            <div style={{ fontSize:14, fontWeight:800, color:c, fontFamily:'var(--mono)' }}>{v}</div>
          </div>
        ))}
      </div>

      {/* Indicators */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
        <div>
          <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:2, marginBottom:8 }}>4H CHART</div>
          <DataRow label="Trend"     value={t4.l||trend_4h}                    color={t4.c}                        />
          <DataRow label="ADX (14)"  value={adx}                               color={adxC(adx)}                   />
          <DataRow label="ATR (14)"  value={atr?.toFixed(5)}                   color="var(--cyan)"                 />
          <DataRow label="EMA 21"    value={ema_4h?.toFixed(5)}                color="var(--t1)"                   />
          <DataRow label="vs EMA"    value={above_ema_4h?'ABOVE ↑':'BELOW ↓'} color={above_ema_4h?'var(--green)':'var(--red)'} />
          <DataRow label="Max Stop"  value={(atr*1.5).toFixed(5)}              color="var(--amber)"                />
        </div>
        <div>
          <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:2, marginBottom:8 }}>1H CHART</div>
          <DataRow label="Trend"      value={t1.l||trend_1h}                    color={t1.c}                       />
          <DataRow label="ADX (14)"   value={adx_1h}                            color={adxC(adx_1h)}               />
          <DataRow label="ATR (14)"   value={atr_1h?.toFixed(5)}               color="var(--cyan)"                 />
          <DataRow label="Session"    value={session?.label}                    color="var(--t1)"                   />
          <DataRow label="Volatility" value={volatility?.replace('_',' ').toUpperCase()} color={V_COLOR[volatility]}/>
          <DataRow label="TF Agree"   value={aligned?'YES ✓':'NO ✗'}           color={aligned?'var(--green)':'var(--red)'} />
        </div>
      </div>

      {!aligned   && <Alert type="block" style={{ marginTop:10 }}>✗ 4H/1H conflict — AI blocked per Rule 2</Alert>}
      {session?.quality==='avoid' && <Alert type="warn" style={{ marginTop:8 }}>⚠ {session.label} — thin session, trades likely blocked</Alert>}

      {/* News strip */}
      {news?.risk && (
        <div style={{ marginTop:10, padding:'8px 12px', borderRadius:7, background:'var(--card)', border:'1px solid var(--b0)', display:'flex', alignItems:'center', justifyContent:'space-between' }}>
          <div>
            <div style={{ fontSize:8, color:'var(--t2)', fontFamily:'var(--mono)', letterSpacing:1, marginBottom:2 }}>NEWS RISK</div>
            <div style={{ fontSize:10, fontFamily:'var(--mono)', fontWeight:600, color: ['snb_block','hard_block','window_block'].includes(news.risk.level)?'var(--red-hi)':news.risk.level==='caution'?'var(--amber-hi)':'var(--green)' }}>{news.risk.label}</div>
          </div>
          <Tag type={['snb_block','hard_block','window_block'].includes(news.risk.level)?'block':news.risk.level==='caution'?'warn':news.risk.level==='clear'?'ok':'muted'}>
            {news.risk.level.toUpperCase().replace(/_/g,' ')}
          </Tag>
        </div>
      )}
    </Panel>
  )
}
