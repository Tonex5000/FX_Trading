"""
OANDA v20 REST API service.
Fetches live USD/CHF price + candle data, then auto-calculates
all technical indicators needed by the AI.

Docs: https://developer.oanda.com/rest-live-v20/instrument-ep/
"""
from datetime import datetime, timezone
import httpx
from core.config import get_settings
from services.indicators import calc_atr, calc_adx, detect_trend, classify_volatility
from models.schemas import MarketData, PriceData, SessionInfo

INSTRUMENT = "USD_CHF"


def _detect_session() -> SessionInfo:
    now  = datetime.now(timezone.utc)
    hour = now.hour
    mins = now.minute
    t    = hour + mins / 60

    if   0  <= t <  8:  return SessionInfo(id="asian",        label="Asian",       quality="avoid")
    elif 8  <= t < 10:  return SessionInfo(id="london_open",  label="London Open", quality="optimal")
    elif 10 <= t < 12:  return SessionInfo(id="london_mid",   label="London Mid",  quality="good")
    elif 12 <= t < 17:  return SessionInfo(id="ny_overlap",   label="NY Overlap",  quality="good")
    elif 17 <= t < 21:  return SessionInfo(id="ny_close",     label="NY Close",    quality="caution")
    else:               return SessionInfo(id="off_hours",    label="Off Hours",   quality="avoid")


async def _fetch_candles(client: httpx.AsyncClient, granularity: str, count: int = 60) -> list[dict]:
    """Fetch OHLC candles from OANDA."""
    cfg = get_settings()
    url = f"{cfg.oanda_base_url}/v3/instruments/{INSTRUMENT}/candles"
    params = {"granularity": granularity, "count": count, "price": "M"}
    resp = await client.get(url, headers=cfg.oanda_headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "time":  c["time"],
            "open":  float(c["mid"]["o"]),
            "high":  float(c["mid"]["h"]),
            "low":   float(c["mid"]["l"]),
            "close": float(c["mid"]["c"]),
        }
        for c in data["candles"]
        if c.get("complete", True)
    ]


async def _fetch_price(client: httpx.AsyncClient) -> PriceData:
    """Fetch latest bid/ask from OANDA."""
    cfg = get_settings()
    url = f"{cfg.oanda_base_url}/v3/instruments/{INSTRUMENT}/candles"
    params = {"granularity": "S5", "count": 1, "price": "BA"}
    resp = await client.get(url, headers=cfg.oanda_headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    last = data["candles"][-1]
    bid  = float(last["bid"]["c"])
    ask  = float(last["ask"]["c"])
    mid  = round((bid + ask) / 2, 5)
    return PriceData(bid=bid, ask=ask, mid=mid, spread=round(ask - bid, 5))


async def fetch_market_data() -> MarketData:
    """
    Main entry point — fetches all OANDA data concurrently and
    returns a complete MarketData object with all indicators computed.
    """
    cfg = get_settings()
    async with httpx.AsyncClient(timeout=15.0) as client:
        import asyncio
        candles_4h, candles_1h, price = await asyncio.gather(
            _fetch_candles(client, "H4", 60),
            _fetch_candles(client, "H1", 60),
            _fetch_price(client),
        )

    # Calculate all indicators
    atr_4h   = calc_atr(candles_4h)
    atr_1h   = calc_atr(candles_1h)
    adx_4h   = calc_adx(candles_4h)
    adx_1h   = calc_adx(candles_1h)
    trend_4h = detect_trend(candles_4h)
    trend_1h = detect_trend(candles_1h)
    vol      = classify_volatility(candles_4h, atr_4h)
    session  = _detect_session()

    return MarketData(
        price       = price,
        adx         = adx_4h,
        adx_1h      = adx_1h,
        atr         = atr_4h,
        atr_1h      = atr_1h,
        trend_4h    = trend_4h["direction"],
        trend_1h    = trend_1h["direction"],
        ema_4h      = trend_4h["ema"],
        above_ema_4h= trend_4h["above_ema"],
        volatility  = vol,
        session     = session,
        fetched_at  = datetime.now(timezone.utc),
    )
