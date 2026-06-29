"""
Bot API Router
==============
All endpoints to control and monitor the trading bot.

POST /api/bot/start          — start the bot with optional config
POST /api/bot/stop           — stop the bot
GET  /api/bot/status         — live status + open trade
GET  /api/bot/history        — last 100 run results
POST /api/bot/run-once       — run a single cycle immediately (manual trigger)
POST /api/bot/close-trade    — emergency close of open trade
"""
from fastapi import APIRouter, HTTPException
from bot.engine  import start_bot, stop_bot, get_status, get_history, _run_cycle
from bot.executor import close_trade, get_open_trade
from bot.schemas  import BotConfig, BotStatus, BotRunResult

router = APIRouter(prefix="/api/bot", tags=["Trading Bot"])


@router.post("/start", response_model=BotStatus, summary="Start the trading bot")
async def bot_start(config: BotConfig | None = None):
    """
    Start the automated trading bot.

    The bot will:
    - Run every `scan_interval_secs` seconds (default: 300 = 5 min)
    - Fetch live OANDA data + ForexFactory news
    - Ask Groq AI (qwen3-32b) for a trade signal
    - Place a trade on OANDA only if:
        - Signal is BUY or SELL
        - Confidence ≥ `min_confidence` (default: 70%)
        - Filters passed ≥ `min_filters` (default: 7/9)
        - No open trade already exists (if `allow_one_trade=true`)
    """
    try:
        await start_bot(config)
        return get_status()
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/stop", response_model=BotStatus, summary="Stop the trading bot")
async def bot_stop():
    """Stop the bot. Does NOT close any open trades."""
    try:
        await stop_bot()
        return get_status()
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/status", response_model=BotStatus, summary="Live bot status")
async def bot_status():
    """Returns current bot state including open trade and last run result."""
    status = get_status()
    # Refresh open trade from OANDA on every status check
    try:
        status.open_trade = await get_open_trade()
    except Exception:
        pass
    return status


@router.get("/history", response_model=list[BotRunResult], summary="Bot run history")
async def bot_history():
    """Returns the last 100 bot cycle results, most recent first."""
    return get_history()


@router.post("/run-once", response_model=BotRunResult, summary="Run one cycle immediately")
async def bot_run_once():
    """
    Manually trigger a single analysis + trade cycle right now,
    regardless of the scan interval. Useful for testing.
    The bot does NOT need to be running to use this endpoint.
    """
    cfg = get_status().config
    result = await _run_cycle(cfg)
    return result


@router.post("/close-trade", summary="Emergency close open trade")
async def bot_close_trade():
    """
    Immediately close the current open USD/CHF trade on OANDA.
    Use this for emergency exits.
    """
    status = get_status()
    trade  = status.open_trade

    if not trade or not trade.oanda_trade_id:
        # Try to fetch fresh from OANDA
        trade = await get_open_trade()
        if not trade:
            raise HTTPException(status_code=404, detail="No open trade found.")

    try:
        result = await close_trade(trade.oanda_trade_id)
        status.open_trade = None
        return {
            "message":  f"Trade {trade.oanda_trade_id} closed successfully.",
            "oanda_response": result,
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Close trade failed: {e}")
