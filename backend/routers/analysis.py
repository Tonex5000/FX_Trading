import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from models.schemas import AnalyzeRequest, AnalyzeResponse
from services.pepperstone import fetch_market_data
from services.news  import fetch_news_data
from services.groq import run_ai_analysis

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post("/analyze", response_model=AnalyzeResponse, summary="Full AI trade signal")
async def analyze(req: AnalyzeRequest):
    """
    Runs the complete 3-step analysis pipeline:

    **Step 1** — Fetch live USD/CHF market data from OANDA  
    (price, candles, ADX, ATR, EMA 21, trend, session)

    **Step 2** — Fetch economic calendar from ForexFactory  
    (upcoming USD/CHF events, SNB detection, risk level)

    **Step 3** — Send everything to Groq AI (qwen/qwen3-32b)  
    The model applies all 7 trading rules and returns:
    - BUY / SELL / NO TRADE signal
    - Entry, stop-loss, take-profit prices
    - Dynamic position size (0.5% or 1.0%)
    - 9-point confluence check
    - Plain-English reasoning + trade execution plan
    """
    try:
        # Step 1 + 2 run concurrently — saves ~2 seconds
        market, news = await asyncio.gather(
            fetch_market_data(),
            fetch_news_data(),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Data fetch failed: {str(e)}")

    try:
        signal = await run_ai_analysis(market, news, req.account_balance)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI analysis failed: {str(e)}")

    return AnalyzeResponse(
        market      = market,
        news        = news,
        signal      = signal,
        analyzed_at = datetime.now(timezone.utc),
    )
