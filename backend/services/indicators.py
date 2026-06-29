"""
Pure technical indicator calculations.
All functions operate on lists of OHLC dicts.
No external dependencies — only the Python standard library.
"""
from typing import TypedDict


class Candle(TypedDict):
    time: str
    open: float
    high: float
    low: float
    close: float


def calc_ema(values: list[float], period: int) -> float:
    """Exponential Moving Average (EMA)."""
    if len(values) < period:
        return values[-1] if values else 0.0
    k = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for v in values[period:]:
        ema = v * k + ema * (1 - k)
    return round(ema, 5)


def calc_atr(candles: list[Candle], period: int = 14) -> float:
    """Average True Range — Wilder's smoothing method."""
    if len(candles) < period + 1:
        return 0.0

    trs = []
    for i, c in enumerate(candles):
        if i == 0:
            trs.append(c["high"] - c["low"])
            continue
        prev_close = candles[i - 1]["close"]
        tr = max(
            c["high"] - c["low"],
            abs(c["high"] - prev_close),
            abs(c["low"]  - prev_close),
        )
        trs.append(tr)

    # Wilder smoothing
    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period

    return round(atr, 5)


def calc_adx(candles: list[Candle], period: int = 14) -> int:
    """Average Directional Index (ADX)."""
    if len(candles) < period * 2:
        return 0

    dms = []
    for i, c in enumerate(candles):
        if i == 0:
            dms.append({"plus": 0.0, "minus": 0.0, "tr": c["high"] - c["low"]})
            continue
        prev = candles[i - 1]
        up_move   = c["high"] - prev["high"]
        down_move = prev["low"] - c["low"]
        tr = max(
            c["high"] - c["low"],
            abs(c["high"] - prev["close"]),
            abs(c["low"]  - prev["close"]),
        )
        dms.append({
            "plus":  up_move   if up_move > down_move   and up_move > 0   else 0.0,
            "minus": down_move if down_move > up_move   and down_move > 0 else 0.0,
            "tr":    tr,
        })

    # Initial Wilder averages
    smooth_tr    = sum(d["tr"]    for d in dms[1:period + 1])
    smooth_plus  = sum(d["plus"]  for d in dms[1:period + 1])
    smooth_minus = sum(d["minus"] for d in dms[1:period + 1])

    dx_values = []
    for dm in dms[period + 1:]:
        smooth_tr    = smooth_tr    - smooth_tr    / period + dm["tr"]
        smooth_plus  = smooth_plus  - smooth_plus  / period + dm["plus"]
        smooth_minus = smooth_minus - smooth_minus / period + dm["minus"]

        if smooth_tr == 0:
            continue
        pdi = (smooth_plus  / smooth_tr) * 100
        mdi = (smooth_minus / smooth_tr) * 100
        denom = pdi + mdi
        dx_values.append(abs(pdi - mdi) / denom * 100 if denom else 0)

    if not dx_values:
        return 0

    adx = sum(dx_values[-period:]) / min(period, len(dx_values))
    return round(adx)


def detect_trend(candles: list[Candle], ema_period: int = 21) -> dict:
    """
    Classify trend direction as one of:
    strong_up | weak_up | ranging | weak_down | strong_down
    """
    closes = [c["close"] for c in candles]
    ema    = calc_ema(closes, ema_period)
    last   = closes[-1]

    # 5-candle slope
    window = closes[-6:-1] if len(closes) >= 6 else closes
    rising  = all(window[i] <= window[i + 1] for i in range(len(window) - 1))
    falling = all(window[i] >= window[i + 1] for i in range(len(window) - 1))

    # % move over 5 candles
    base = closes[-6] if len(closes) >= 6 else closes[0]
    pct  = ((last - base) / base) * 100 if base else 0

    above_ema = last > ema

    if above_ema and rising  and pct >  0.15: direction = "strong_up"
    elif above_ema           and pct >  0.05: direction = "weak_up"
    elif not above_ema and falling and pct < -0.15: direction = "strong_down"
    elif not above_ema       and pct < -0.05: direction = "weak_down"
    else:                                      direction = "ranging"

    return {
        "direction": direction,
        "ema":       ema,
        "last_close": last,
        "above_ema": above_ema,
    }


def classify_volatility(candles: list[Candle], atr: float) -> str:
    """Compare current ATR to 30-candle average range."""
    if len(candles) < 5:
        return "medium"
    avg_range = sum(c["high"] - c["low"] for c in candles[-30:]) / min(30, len(candles))
    if avg_range == 0:
        return "medium"
    ratio = atr / avg_range
    if ratio < 0.5:   return "very_low"
    if ratio < 0.8:   return "low"
    if ratio < 1.2:   return "medium"
    if ratio < 1.6:   return "high"
    return "extreme"
