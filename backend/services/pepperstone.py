"""
Pepperstone cTrader Open API Service
======================================
Handles:
  1. Market data (EUR/CHF price + candles) — with Twelve Data fallback
  2. Trade execution (place orders, manage positions)

Pepperstone uses the cTrader Open API (REST + OAuth2).
Nigerian traders are fully supported via Pepperstone Bahamas (SCB regulated).

Setup:
  1. Open a Pepperstone account: https://www.pepperstone.com
  2. Create a cTrader account in your Pepperstone portal
  3. Go to: https://openapi.ctrader.com → register your app → get client_id + client_secret
  4. Authorize your account to get an access_token

cTrader Open API Docs: https://help.ctrader.com/open-api/
cTrader REST endpoint: https://api.ctrader.com/
"""
import httpx
import asyncio
import logging
from datetime import datetime, timezone
from core.config import get_settings
from services.indicators import calc_atr, calc_adx, detect_trend, classify_volatility
from services.twelvedata import fetch_market_data_fallback
from models.schemas import MarketData, PriceData, SessionInfo
from bot.schemas import TradeOrder

log = logging.getLogger("pepperstone")

INSTRUMENT      = "EURCHF"          # cTrader symbol format (no slash)
INSTRUMENT_DISP = "EUR/CHF"         # human-readable
CT_BASE         = "https://api.ctrader.com"

# cTrader granularity codes
GRAN_MAP = {
    "H4": "h4",
    "H1": "h1",
    "M5": "m5",
}


def _detect_session() -> SessionInfo:
    now = datetime.now(timezone.utc)
    t   = now.hour + now.minute / 60
    if   0  <= t <  8:  return SessionInfo(id="asian",       label="Asian",       quality="avoid")
    elif 8  <= t < 10:  return SessionInfo(id="london_open", label="London Open", quality="optimal")
    elif 10 <= t < 12:  return SessionInfo(id="london_mid",  label="London Mid",  quality="good")
    elif 12 <= t < 17:  return SessionInfo(id="ny_overlap",  label="NY Overlap",  quality="good")
    elif 17 <= t < 21:  return SessionInfo(id="ny_close",    label="NY Close",    quality="caution")
    else:               return SessionInfo(id="off_hours",   label="Off Hours",   quality="avoid")


def _ctrader_headers() -> dict:
    cfg = get_settings()
    return {
        "Authorization": f"Bearer {cfg.ctrader_access_token}",
        "Content-Type":  "application/json",
    }


async def _get_account_id(client: httpx.AsyncClient) -> str:
    """Fetch cTrader account ID."""
    cfg  = get_settings()
    if cfg.ctrader_account_id:
        return cfg.ctrader_account_id

    resp = await client.get(
        f"{CT_BASE}/account",
        headers=_ctrader_headers(),
        timeout=10.0,
    )
    resp.raise_for_status()
    accounts = resp.json().get("data", [])
    if not accounts:
        raise RuntimeError("No cTrader accounts found.")
    return str(accounts[0]["tradingAccountId"])


async def _fetch_candles_ct(
    client:      httpx.AsyncClient,
    account_id:  str,
    granularity: str,
    count:       int = 60,
) -> list[dict]:
    """Fetch OHLC bars from cTrader Open API."""
    resp = await client.get(
        f"{CT_BASE}/account/{account_id}/symbol/{INSTRUMENT}/bars",
        headers=_ctrader_headers(),
        params={
            "granularity": GRAN_MAP.get(granularity, "h1"),
            "count":       count,
        },
        timeout=15.0,
    )
    resp.raise_for_status()
    bars = resp.json().get("data", [])
    return [
        {
            "time":  b["timestamp"],
            "open":  float(b["open"]),
            "high":  float(b["high"]),
            "low":   float(b["low"]),
            "close": float(b["close"]),
        }
        for b in bars
    ]


async def _fetch_price_ct(client: httpx.AsyncClient) -> PriceData:
    """Fetch live EUR/CHF bid/ask from cTrader."""
    resp = await client.get(
        f"{CT_BASE}/symbol/{INSTRUMENT}/quote",
        headers=_ctrader_headers(),
        timeout=10.0,
    )
    resp.raise_for_status()
    d   = resp.json().get("data", {})
    bid = float(d.get("bid", 0))
    ask = float(d.get("ask", 0))
    mid = round((bid + ask) / 2, 5)
    return PriceData(bid=bid, ask=ask, mid=mid, spread=round(ask - bid, 5))


# ── Main market data fetch with Twelve Data fallback ─────────────────────

async def fetch_market_data() -> MarketData:
    """
    Fetch EUR/CHF market data from Pepperstone cTrader Open API.

    If cTrader is unavailable (network error, auth issue, maintenance),
    automatically falls back to Twelve Data and logs a warning.
    The rest of the system receives identical MarketData either way.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            account_id = await _get_account_id(client)
            candles_4h, candles_1h, price = await asyncio.gather(
                _fetch_candles_ct(client, account_id, "H4", 60),
                _fetch_candles_ct(client, account_id, "H1", 60),
                _fetch_price_ct(client),
            )

        log.info(f"Market data from Pepperstone cTrader — EUR/CHF {price.mid}")

    except Exception as primary_err:
        log.warning(
            f"Pepperstone cTrader fetch failed ({primary_err}). "
            f"Falling back to Twelve Data…"
        )
        try:
            return await fetch_market_data_fallback()
        except Exception as fallback_err:
            raise RuntimeError(
                f"Both data sources failed. "
                f"Pepperstone: {primary_err} | "
                f"Twelve Data: {fallback_err}"
            )

    atr_4h   = calc_atr(candles_4h)
    atr_1h   = calc_atr(candles_1h)
    adx_4h   = calc_adx(candles_4h)
    adx_1h   = calc_adx(candles_1h)
    trend_4h = detect_trend(candles_4h)
    trend_1h = detect_trend(candles_1h)
    vol      = classify_volatility(candles_4h, atr_4h)
    session  = _detect_session()

    return MarketData(
        price        = price,
        adx          = adx_4h,
        adx_1h       = adx_1h,
        atr          = atr_4h,
        atr_1h       = atr_1h,
        trend_4h     = trend_4h["direction"],
        trend_1h     = trend_1h["direction"],
        ema_4h       = trend_4h["ema"],
        above_ema_4h = trend_4h["above_ema"],
        volatility   = vol,
        session      = session,
        fetched_at   = datetime.now(timezone.utc),
    )


# ── Trade execution via cTrader Open API ─────────────────────────────────

async def get_account_balance() -> float:
    """Fetch live account balance from cTrader."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        account_id = await _get_account_id(client)
        resp = await client.get(
            f"{CT_BASE}/account/{account_id}",
            headers=_ctrader_headers(),
            timeout=10.0,
        )
        resp.raise_for_status()
        data    = resp.json().get("data", {})
        balance = float(data.get("balance", 0)) / 100   # cTrader returns cents
        return balance


async def get_open_trade() -> TradeOrder | None:
    """Check for an open EUR/CHF position on cTrader."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        account_id = await _get_account_id(client)
        resp = await client.get(
            f"{CT_BASE}/account/{account_id}/position",
            headers=_ctrader_headers(),
            timeout=10.0,
        )
        resp.raise_for_status()
        positions = resp.json().get("data", [])

    # Filter to EUR/CHF open positions
    eurchf = [p for p in positions if p.get("symbol", "").upper() == INSTRUMENT]
    if not eurchf:
        return None

    p    = eurchf[0]
    side = "BUY" if p.get("tradeSide", "").upper() == "BUY" else "SELL"

    return TradeOrder(
        oanda_order_id     = str(p.get("positionId", "")),
        oanda_trade_id     = str(p.get("positionId", "")),
        instrument         = INSTRUMENT_DISP,
        side               = side,
        units              = float(p.get("volume", 0)) / 100,
        entry_price        = float(p.get("entryPrice", 0)),
        stop_loss          = float(p.get("stopLoss", 0)),
        take_profit_1      = float(p.get("takeProfit", 0)),
        risk_percent       = 0.0,
        risk_amount_usd    = 0.0,
        position_size_lots = float(p.get("volume", 0)) / 100_000,
        placed_at          = datetime.now(timezone.utc),
        status             = "OPEN",
    )


async def place_order(
    side:               str,
    units:              float,
    stop_loss:          float,
    take_profit_1:      float,
    take_profit_2:      float | None,
    entry_price:        float,
    risk_percent:       float,
    risk_amount_usd:    float,
    position_size_lots: float,
) -> TradeOrder:
    """
    Place a market order on Pepperstone via cTrader Open API.

    cTrader volume is in units:
      1 standard lot = 100,000 units
      0.01 lot       = 1,000 units (micro lot)
    """
    cfg     = get_settings()
    ct_vol  = int(units * 100_000)   # convert lots to cTrader units

    order_body = {
        "symbolName":  INSTRUMENT,
        "tradeSide":   "BUY" if side == "BUY" else "SELL",
        "volume":      ct_vol,
        "orderType":   "MARKET",
        "stopLoss":    round(stop_loss, 5),
        "takeProfit":  round(take_profit_1, 5),
        "comment":     "FX-AI-BOT",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        account_id = await _get_account_id(client)
        resp = await client.post(
            f"{CT_BASE}/account/{account_id}/order",
            headers=_ctrader_headers(),
            json=order_body,
            timeout=15.0,
        )

    data = resp.json()

    if not resp.is_success or data.get("errorCode"):
        reason = data.get("description") or data.get("errorCode") or f"HTTP {resp.status_code}"
        raise RuntimeError(f"cTrader order rejected: {reason}")

    order_data  = data.get("data", {})
    position_id = str(order_data.get("positionId", order_data.get("orderId", "")))
    fill_price  = float(order_data.get("executionPrice", entry_price))

    log.info(
        f"Order placed on Pepperstone | {side} EUR/CHF | "
        f"Lots={units} | Price={fill_price} | SL={stop_loss} | TP={take_profit_1} | "
        f"PositionID={position_id}"
    )

    return TradeOrder(
        oanda_order_id     = position_id,
        oanda_trade_id     = position_id,
        instrument         = INSTRUMENT_DISP,
        side               = side,
        units              = ct_vol,
        entry_price        = fill_price,
        stop_loss          = stop_loss,
        take_profit_1      = take_profit_1,
        take_profit_2      = take_profit_2,
        risk_percent       = risk_percent,
        risk_amount_usd    = risk_amount_usd,
        position_size_lots = position_size_lots,
        placed_at          = datetime.now(timezone.utc),
        status             = "OPEN",
    )


async def close_trade(position_id: str) -> dict:
    """Close an open EUR/CHF position on cTrader."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        account_id = await _get_account_id(client)
        resp = await client.delete(
            f"{CT_BASE}/account/{account_id}/position/{position_id}",
            headers=_ctrader_headers(),
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()
