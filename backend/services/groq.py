"""
Groq AI Decision Engine — qwen/qwen3-32b
Receives fully auto-populated OANDA + ForexFactory data
and makes the final trade decision with no human input.

Groq API is OpenAI-compatible, so we use httpx directly
(no SDK dependency needed beyond the groq package).

Docs: https://console.groq.com/docs/openai
Model: qwen/qwen3-32b
"""
import json
import httpx
from core.config import get_settings
from models.schemas import MarketData, NewsData, TradeSignal, ConfluenceCheck

MODEL      = "qwen/qwen3-32b"
MAX_TOKENS = 1500
GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are an elite quantitative FX trading AI. You specialize exclusively in EUR/CHF.
All market data arrives live from OANDA and all news from ForexFactory — there is no human input error.
Apply 7 professional-grade filters and return a final trade decision with surgical precision.
You are disciplined and conservative: missing a trade is always better than taking a bad one.

══════════════════════════════════════════════════════════
RULE 1 — INSTRUMENT
══════════════════════════════════════════════════════════
EUR/CHF only. Safe-haven pair, institutionally liquid. CHF is driven by Swiss economic data
and the SNB (Swiss National Bank). Any SNB event is an absolute black-swan risk.

══════════════════════════════════════════════════════════
RULE 2 — MULTI-TIMEFRAME TREND CONFIRMATION
══════════════════════════════════════════════════════════
4H and 1H trend directions MUST agree:
- strong_up / weak_up = bullish direction
- strong_down / weak_down = bearish direction
- ranging = neutral
If 4H is bullish and 1H is bearish (or vice versa) → NO TRADE immediately.
EMA 21 on 4H: price above = uptrend valid, below = downtrend valid.
If price is AT the EMA → ambiguous → NO TRADE.
Entry must be a pullback or retest, NOT a breakout chase. Breakout = reduce confidence by 15.

══════════════════════════════════════════════════════════
RULE 3 — ADX REGIME FILTER
══════════════════════════════════════════════════════════
Use 4H ADX as primary, 1H ADX as confirmation.
- ADX >= 25: TRENDING — full system operation, 1.0% risk eligible
- ADX 20-24: BORDERLINE — max 0.5% risk, confidence must be >= 68
- ADX < 20:  CHOPPY — NO TRADE unconditionally. Choppy markets destroy systematic strategies.

══════════════════════════════════════════════════════════
RULE 4 — NEWS & SNB FILTER (LIVE FROM FOREXFACTORY)
══════════════════════════════════════════════════════════
Apply these rules based on the news_risk.level field you receive:
- snb_block:     ABSOLUTE NO TRADE. SNB can move EUR/CHF 200-400 pips instantly.
- hard_block:    NO TRADE. High-impact USD or CHF event (NFP, CPI, FOMC, GDP).
- window_block:  NO TRADE. Significant event within 30 minutes either side.
- caution:       Allowed but MUST use 0.5% risk and add explicit warning.
- clear/unknown: Proceed and apply remaining filters normally.

══════════════════════════════════════════════════════════
RULE 5 — SESSION FILTER
══════════════════════════════════════════════════════════
- london_open (08:00-10:00 GMT): OPTIMAL. Best institutional flow for EUR/CHF.
- london_mid  (10:00-12:00 GMT): GOOD.
- ny_overlap  (12:00-17:00 GMT): GOOD. Strong USD participation.
- asian       (00:00-08:00 GMT): AVOID — thin liquidity, SNB intervention zone. NO TRADE.
- ny_close    (17:00-21:00 GMT): CAUTION — spread widens, liquidity drops.
- off_hours:                      NO TRADE unconditionally.

══════════════════════════════════════════════════════════
RULE 6 — ATR-BASED STOP LOSS VALIDATION
══════════════════════════════════════════════════════════
ATR is auto-calculated from OANDA candles (Wilder's method, 14-period, 4H).
- Maximum allowable stop distance = ATR x 1.5
- Stop must be placed at a structural level (swing low for BUY, swing high for SELL)
- If structure requires wider stop than ATR x 1.5 → NO TRADE (too noisy)
- Minimum R:R = 1:2. Take-profit must be at least 2x the stop distance.
- If 1:2 R:R not achievable within ATR constraints → NO TRADE

Position size formula (EUR/CHF, 1 pip = 0.0001, pip value approx $10/lot standard):
  lots = (account_balance x risk_percent / 100) / (stop_pips x 10)

══════════════════════════════════════════════════════════
RULE 7 — DYNAMIC POSITION SIZING
══════════════════════════════════════════════════════════
1.0% risk: ALL pass — ADX >= 25, confidence >= 75, optimal/good session, clear news, trends strongly aligned
0.5% risk: ADX 20-24 OR confidence 65-74 OR acceptable session OR medium news OR one minor issue
NO TRADE:  confidence < 65, any hard filter fails, 1:2 R:R not achievable

══════════════════════════════════════════════════════════
CRITICAL RESPONSE FORMAT
══════════════════════════════════════════════════════════
You MUST return ONLY a valid JSON object.
- No markdown
- No code fences (no backticks)
- No <think> tags or reasoning text
- No explanation before or after the JSON
- Start your response with { and end with }

{
  "signal": "BUY" or "SELL" or "NO TRADE",
  "confidence": integer 0-100,
  "market_condition": "TRENDING_UP" or "TRENDING_DOWN" or "RANGING" or "CHOPPY" or "HIGH_VOLATILITY" or "NEWS_RISK" or "SNB_RISK" or "WRONG_SESSION" or "TF_CONFLICT",
  "regime": "TRENDING" or "BORDERLINE" or "CHOPPY",
  "entry_price": number or null,
  "stop_loss": number or null,
  "take_profit_1": number or null,
  "take_profit_2": number or null,
  "stop_basis": "SWING_LOW" or "SWING_HIGH" or "EMA_21" or "ATR_1.5x" or null,
  "risk_reward": "1:2" or "1:2.5" or "1:3" or "N/A",
  "risk_percent": 0.5 or 1.0 or null,
  "position_size_lots": number or null,
  "stop_pips": integer or null,
  "tp1_pips": integer or null,
  "confluence_check": {
    "tf_4h_1h_agree": true or false,
    "ema21_aligned": true or false,
    "adx_regime_valid": true or false,
    "pullback_entry": true or false,
    "session_valid": true or false,
    "news_window_clear": true or false,
    "snb_risk_clear": true or false,
    "stop_within_atr15": true or false,
    "rr_minimum_1to2": true or false
  },
  "filters_passed": integer 0-9,
  "auto_data_quality": "HIGH" or "MEDIUM" or "LOW",
  "reasoning": "2-3 sentences citing specific values e.g. ADX=31 ATR=0.0038 4H strong_up 1H weak_up aligned",
  "trade_plan": "Step-by-step execution if signal. If NO TRADE: specific conditions to watch for.",
  "blocked_by": "Primary block reason with value e.g. ADX=17 below minimum 20 or null if signal issued",
  "market_context": "1 sentence on current EUR/CHF macro and CHF safe-haven status",
  "news_assessment": "Your interpretation of news risk and which events matter and why",
  "next_check": "When to re-run analysis e.g. After NFP at 13:30 GMT or After London open at 08:00",
  "warnings": ["specific actionable warning strings"]
}"""


def _build_prompt(market: MarketData, news: NewsData, balance: float) -> str:
    upcoming = "\n".join(
        f"  - [{e.currency}] {e.title} | Impact: {e.impact} | "
        f"{'In ' + str(e.mins_away) + 'min' if e.mins_away > 0 else str(abs(e.mins_away)) + 'min ago'} | "
        f"Status: {e.block_status}"
        for e in news.events[:8]
    ) or "  No significant EUR/CHF events in the next 24 hours"

    return f"""All data is live. OANDA for market, ForexFactory for news. No human input.

=== LIVE MARKET DATA (OANDA) ===
Instrument:      EUR/CHF
Mid Price:       {market.price.mid}
Bid / Ask:       {market.price.bid} / {market.price.ask}
Spread:          {round(market.price.spread * 10000, 1)} pips
Fetched at:      {market.fetched_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

4H Analysis:
  Trend:         {market.trend_4h}
  ADX (14):      {market.adx}
  ATR (14):      {market.atr}
  EMA 21:        {market.ema_4h}  — price is {'ABOVE' if market.above_ema_4h else 'BELOW'} EMA
  Max stop:      {round(market.atr * 1.5, 5)} (ATR x 1.5)

1H Analysis:
  Trend:         {market.trend_1h}
  ADX (14):      {market.adx_1h}
  ATR (14):      {market.atr_1h}

Session:         {market.session.id} — {market.session.label} [{market.session.quality.upper()}]
Volatility:      {market.volatility}

=== NEWS DATA (FOREXFACTORY) ===
Risk Level:      {news.risk.level.upper()} — {news.risk.label}
Fetched at:      {news.fetched_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

Upcoming EUR/CHF Events (next 24h):
{upcoming}

=== ACCOUNT ===
Balance:         ${balance:,.2f}
Max risk 0.5%:   ${balance * 0.005:,.2f}
Max risk 1.0%:   ${balance * 0.01:,.2f}

Apply all 7 filters using the live data above and return your JSON decision.
Remember: respond with ONLY the JSON object, nothing else."""


def _extract_json(raw: str) -> str:
    """
    Qwen3 models sometimes emit <think>...</think> reasoning blocks
    before the actual JSON. Strip them out before parsing.
    Also handles any stray markdown fences.
    """
    import re

    # Remove <think>...</think> blocks (Qwen3 chain-of-thought)
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)

    # Remove markdown fences
    raw = raw.replace("```json", "").replace("```", "")

    # Extract the first complete JSON object
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in model response")

    return raw[start:end].strip()


async def run_ai_analysis(market: MarketData, news: NewsData, balance: float) -> TradeSignal:
    """
    Send live market + news data to Groq (qwen/qwen3-32b) and parse the trade signal.
    Uses Groq's OpenAI-compatible REST API via httpx.
    """
    cfg    = get_settings()
    prompt = _build_prompt(market, news, balance)

    payload = {
        "model":       MODEL,
        "max_tokens":  MAX_TOKENS,
        "temperature": 0.1,          # low temp = deterministic, rule-following
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {cfg.groq_api_key}",
                "Content-Type":  "application/json",
            },
            json=payload,
        )

    if not resp.is_success:
        err = resp.json() if resp.headers.get("content-type","").startswith("application/json") else {}
        raise RuntimeError(f"Groq API error {resp.status_code}: {err.get('error', {}).get('message', resp.text)}")

    raw   = resp.json()["choices"][0]["message"]["content"]
    clean = _extract_json(raw)
    data  = json.loads(clean)

    # Build ConfluenceCheck from nested dict
    cc = data.pop("confluence_check", {})
    data["confluence_check"] = ConfluenceCheck(**cc)

    return TradeSignal(**data)
