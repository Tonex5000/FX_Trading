"""
Twelve Data Fallback Market Service
=====================================
Used as a fallback when the primary broker (Pepperstone/cTrader) fails
to return market data for EUR/CHF.

Twelve Data free tier:
  - 8 API calls/minute, 800/day
  - No credit card required for basic forex data
  - EUR/CHF supported on all tiers

Docs: https://twelvedata.com/docs
"""
import httpx
from datetime import datetime, timezone
from core.config import get_settings
from services.indicators import calc_atr, calc_adx, detect_trend, classify_volatility
from models.schemas import MarketData, PriceData, SessionInfo

INSTRUMENT  = "EUR/CHF"
TD_BASE_URL = "https://api.twelvedata.com"


def _detect_session() -> SessionInfo:
    now = datetime.now(timezone.utc)
    t   = now.hour + now.minute / 60
    if   0  <= t <  8:  return SessionInfo(id="asian",       label="Asian",       quality="avoid")
    elif 8  <= t < 10:  return SessionInfo(id="london_open", label="London Open", quality="optimal")
    elif 10 <= t < 12:  return SessionInfo(id="london_mid",  label="London Mid",  quality="good")
    elif 12 <= t < 17:  return SessionInfo(id="ny_overlap",  label="NY Overlap",  quality="good")
    elif 17 <= t < 21:  return SessionInfo(id="ny_close",    label="NY Close",    quality="caution")
    else:               return SessionInfo(id="off_hours",   label="Off Hours",   quality="avoid")


async def _fetch_candles_td(client: httpx.AsyncClient, interval: str, outputsize: int = 60) -> list[dict]:
    """
    Fetch OHLC candles from Twelve Data.
    interval: '4h' | '1h'
    """
    cfg    = get_settings()
    params = {
        "symbol":     INSTRUMENT,
        "interval":   interval,
        "outputsize": outputsize,
        "apikey":     cfg.twelve_data_api_key,
        "format":     "JSON",
    }
    resp = await client.get(f"{TD_BASE_URL}/time_series", params=params, timeout=12.0)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") == "error":
        raise RuntimeError(f"Twelve Data error: {data.get('message', 'Unknown error')}")

    return [
        {
            "time":  c["datetime"],
            "open":  float(c["open"]),
            "high":  float(c["high"]),
            "low":   float(c["low"]),
            "close": float(c["close"]),
        }
        for c in reversed(data.get("values", []))   # TD returns newest first
    ]


async def _fetch_price_td(client: httpx.AsyncClient) -> PriceData:
    """Fetch latest EUR/CHF quote from Twelve Data."""
    cfg    = get_settings()
    params = {
        "symbol": INSTRUMENT,
        "apikey": cfg.twelve_data_api_key,
    }
    resp = await client.get(f"{TD_BASE_URL}/price", params=params, timeout=10.0)
    resp.raise_for_status()
    data  = resp.json()

    if data.get("status") == "error":
        raise RuntimeError(f"Twelve Data price error: {data.get('message')}")

    mid = float(data["price"])
    # Twelve Data free tier doesn't give bid/ask — use small estimate
    spread = 0.0002   # typical EUR/CHF spread ~2 pips
    return PriceData(
        bid    = round(mid - spread / 2, 5),
        ask    = round(mid + spread / 2, 5),
        mid    = round(mid, 5),
        spread = spread,
    )


async def fetch_market_data_fallback() -> MarketData:
    """
    Fallback market data fetch using Twelve Data.
    Called automatically when Pepperstone/cTrader fetch fails.
    Returns same MarketData schema — the rest of the system is unaware
    of which source provided the data.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        import asyncio
        candles_4h, candles_1h, price = await asyncio.gather(
            _fetch_candles_td(client, "4h", 60),
            _fetch_candles_td(client, "1h", 60),
            _fetch_price_td(client),
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
