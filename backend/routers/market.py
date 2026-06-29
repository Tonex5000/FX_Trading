from fastapi import APIRouter, HTTPException
from models.schemas import MarketData
from services.pepperstone import fetch_market_data

router = APIRouter(prefix="/api", tags=["Market"])


@router.get("/market", response_model=MarketData, summary="Live USD/CHF market data")
async def get_market():
    """
    Fetches live EUR/CHF data from Pepperstone cTrader (with Twelve Data fallback) and returns auto-calculated indicators:
    - Current bid/ask/mid price and spread
    - 4H and 1H trend direction
    - ADX (14) — regime detection
    - ATR (14) — stop distance basis
    - EMA 21 — trend alignment
    - Current session and volatility level
    """
    try:
        return await fetch_market_data()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OANDA fetch failed: {str(e)}")
