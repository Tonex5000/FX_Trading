"""
Trading Bot Engine
==================
The core loop that:
  1. Runs the full analysis (OANDA + ForexFactory + Groq AI)
  2. Evaluates the signal against safety thresholds
  3. Places the trade on OANDA if all conditions are met
  4. Monitors open positions for TP2 partial close
  5. Logs every action

Runs as a background asyncio task inside FastAPI.
"""
import asyncio
import uuid
import logging
from datetime import datetime, timezone

from services.pepperstone import fetch_market_data
from services.news   import fetch_news_data
from services.groq   import run_ai_analysis
from bot.executor    import (
    place_order, get_open_trade,
    close_trade, get_account_balance,
)
from bot.schemas     import BotConfig, BotStatus, BotRunResult, TradeOrder
from models.schemas  import TradeSignal

log = logging.getLogger("bot")
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  [BOT]  %(levelname)s  %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)


# ── Global bot state (in-memory, survives process lifetime) ───────────────
_status = BotStatus(
    running       = False,
    config        = BotConfig(),
    total_runs    = 0,
    trades_placed = 0,
)
_history: list[BotRunResult] = []   # last 100 run results
_task: asyncio.Task | None = None


# ── Helpers ───────────────────────────────────────────────────────────────

def get_status()  -> BotStatus:          return _status
def get_history() -> list[BotRunResult]: return list(reversed(_history[-100:]))


def _log_run(result: BotRunResult):
    _history.append(result)
    if len(_history) > 200:
        _history.pop(0)
    _status.last_run    = result
    _status.total_runs += 1
    if result.action == "ORDER_PLACED":
        _status.trades_placed += 1


def _calc_units(
    balance:      float,
    risk_percent: float,
    stop_pips:    int,
) -> tuple[float, float, float]:
    """
    Returns (lots, risk_amount_usd, raw_units_for_oanda)
    USD/CHF: pip_value ≈ $10 per pip per standard lot (100,000 units)
    """
    risk_usd = balance * risk_percent / 100
    pip_val  = 10.0                        # USD per pip per standard lot
    lots     = risk_usd / (stop_pips * pip_val) if stop_pips and stop_pips > 0 else 0.01
    lots     = max(0.01, round(lots, 2))   # minimum 0.01 lot (micro lot)
    return lots, risk_usd, lots * 100_000


# ── Single analysis + execution cycle ─────────────────────────────────────

async def _run_cycle(cfg: BotConfig) -> BotRunResult:
    run_id     = str(uuid.uuid4())[:8]
    started_at = datetime.now(timezone.utc)

    log.info(f"[{run_id}] ── Cycle start ──────────────────────────")

    # ── Guard: skip if trade already open ─────────────────────────────────
    if cfg.allow_one_trade:
        try:
            open_trade = await get_open_trade()
            if open_trade:
                _status.open_trade = open_trade
                msg = f"Open trade already exists (ID {open_trade.oanda_trade_id}) — skipping."
                log.info(f"[{run_id}] {msg}")
                return BotRunResult(
                    run_id=run_id, started_at=started_at,
                    signal="NO TRADE", confidence=0, filters=0,
                    action="SKIPPED_OPEN_TRADE", message=msg,
                    completed_at=datetime.now(timezone.utc),
                )
        except Exception as e:
            log.warning(f"[{run_id}] Could not check open trades: {e}")

    # ── Step 1+2: fetch market + news concurrently ─────────────────────────
    try:
        log.info(f"[{run_id}] Fetching OANDA + ForexFactory…")
        market, news = await asyncio.gather(
            fetch_market_data(),
            fetch_news_data(),
        )
        log.info(f"[{run_id}] Market: {market.price.mid} | ADX={market.adx} | ATR={market.atr} | Session={market.session.id}")
        log.info(f"[{run_id}] News risk: {news.risk.level} — {news.risk.label}")
    except Exception as e:
        msg = f"Market data fetch failed: {e}"
        log.error(f"[{run_id}] {msg}")
        return BotRunResult(
            run_id=run_id, started_at=started_at,
            signal="NO TRADE", confidence=0, filters=0,
            action="ERROR_MARKET", message=msg,
            completed_at=datetime.now(timezone.utc),
        )

    # ── Use live balance if not manually configured ────────────────────────
    try:
        balance = await get_account_balance()
        log.info(f"[{run_id}] Live balance: ${balance:,.2f}")
    except Exception:
        balance = cfg.account_balance
        log.warning(f"[{run_id}] Could not fetch live balance, using config: ${balance:,.2f}")

    # ── Step 3: AI analysis ────────────────────────────────────────────────
    try:
        log.info(f"[{run_id}] Running Groq AI analysis…")
        signal: TradeSignal = await run_ai_analysis(market, news, balance)
        log.info(
            f"[{run_id}] Signal: {signal.signal} | "
            f"Confidence: {signal.confidence}% | "
            f"Filters: {signal.filters_passed}/9 | "
            f"Regime: {signal.regime}"
        )
    except Exception as e:
        msg = f"AI analysis failed: {e}"
        log.error(f"[{run_id}] {msg}")
        return BotRunResult(
            run_id=run_id, started_at=started_at,
            signal="NO TRADE", confidence=0, filters=0,
            action="ERROR_AI", message=msg,
            completed_at=datetime.now(timezone.utc),
        )

    # ── Gate 1: AI said no trade ───────────────────────────────────────────
    if signal.signal == "NO TRADE":
        msg = f"AI: NO TRADE — {signal.blocked_by or signal.reasoning[:80]}"
        log.info(f"[{run_id}] {msg}")
        return BotRunResult(
            run_id=run_id, started_at=started_at,
            signal=signal.signal, confidence=signal.confidence,
            filters=signal.filters_passed, action="NO_TRADE",
            message=msg, completed_at=datetime.now(timezone.utc),
        )

    # ── Gate 2: confidence threshold ──────────────────────────────────────
    if signal.confidence < cfg.min_confidence:
        msg = (
            f"Confidence {signal.confidence}% below minimum {cfg.min_confidence}% — skipped."
        )
        log.info(f"[{run_id}] {msg}")
        return BotRunResult(
            run_id=run_id, started_at=started_at,
            signal=signal.signal, confidence=signal.confidence,
            filters=signal.filters_passed, action="SKIPPED_LOW_CONF",
            message=msg, completed_at=datetime.now(timezone.utc),
        )

    # ── Gate 3: minimum confluence filters ────────────────────────────────
    if signal.filters_passed < cfg.min_filters:
        msg = (
            f"Only {signal.filters_passed}/9 filters passed "
            f"(minimum {cfg.min_filters}) — skipped."
        )
        log.info(f"[{run_id}] {msg}")
        return BotRunResult(
            run_id=run_id, started_at=started_at,
            signal=signal.signal, confidence=signal.confidence,
            filters=signal.filters_passed, action="SKIPPED_LOW_CONF",
            message=msg, completed_at=datetime.now(timezone.utc),
        )

    # ── Gate 4: must have valid price levels ──────────────────────────────
    if not signal.entry_price or not signal.stop_loss or not signal.take_profit_1:
        msg = "AI did not return valid price levels — cannot place order."
        log.warning(f"[{run_id}] {msg}")
        return BotRunResult(
            run_id=run_id, started_at=started_at,
            signal=signal.signal, confidence=signal.confidence,
            filters=signal.filters_passed, action="NO_TRADE",
            message=msg, completed_at=datetime.now(timezone.utc),
        )

    # ── All gates passed — calculate position size and place order ─────────
    risk_pct    = signal.risk_percent or 0.5
    stop_pips   = signal.stop_pips   or 20
    lots, risk_usd, raw_units = _calc_units(balance, risk_pct, stop_pips)

    log.info(
        f"[{run_id}] Placing {signal.signal} order | "
        f"Entry: {signal.entry_price} | SL: {signal.stop_loss} | "
        f"TP1: {signal.take_profit_1} | Lots: {lots} | Risk: ${risk_usd:.2f}"
    )

    try:
        order = await place_order(
            side             = signal.signal,
            units            = lots,
            stop_loss        = signal.stop_loss,
            take_profit_1    = signal.take_profit_1,
            take_profit_2    = signal.take_profit_2,
            entry_price      = signal.entry_price,
            risk_percent     = risk_pct,
            risk_amount_usd  = risk_usd,
            position_size_lots = lots,
        )
        _status.open_trade = order

        msg = (
            f"{signal.signal} order placed — "
            f"TradeID={order.oanda_trade_id} | "
            f"Entry={order.entry_price:.5f} | "
            f"SL={order.stop_loss:.5f} | "
            f"TP1={order.take_profit_1:.5f} | "
            f"Lots={lots} | Risk=${risk_usd:.2f}"
        )
        log.info(f"[{run_id}] ✅ {msg}")

        return BotRunResult(
            run_id=run_id, started_at=started_at,
            signal=signal.signal, confidence=signal.confidence,
            filters=signal.filters_passed, action="ORDER_PLACED",
            order=order, message=msg,
            completed_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        msg = f"OANDA order placement failed: {e}"
        log.error(f"[{run_id}] ❌ {msg}")
        return BotRunResult(
            run_id=run_id, started_at=started_at,
            signal=signal.signal, confidence=signal.confidence,
            filters=signal.filters_passed, action="ERROR_ORDER",
            message=msg, completed_at=datetime.now(timezone.utc),
        )


# ── Main bot loop ──────────────────────────────────────────────────────────

async def _bot_loop():
    cfg = _status.config
    log.info(
        f"Bot started — "
        f"interval={cfg.scan_interval_secs}s | "
        f"min_confidence={cfg.min_confidence}% | "
        f"min_filters={cfg.min_filters}/9"
    )

    while _status.running:
        try:
            result = await _run_cycle(cfg)
            _log_run(result)
        except asyncio.CancelledError:
            break
        except Exception as e:
            log.error(f"Unexpected bot error: {e}", exc_info=True)

        # Wait for next cycle — cancellable
        try:
            log.info(f"Next scan in {cfg.scan_interval_secs}s…")
            await asyncio.sleep(cfg.scan_interval_secs)
        except asyncio.CancelledError:
            break

    log.info("Bot loop stopped.")


# ── Public start / stop API ───────────────────────────────────────────────

async def start_bot(config: BotConfig | None = None):
    global _task
    if _status.running:
        raise RuntimeError("Bot is already running.")

    if config:
        _status.config = config

    _status.running    = True
    _status.started_at = datetime.now(timezone.utc)
    _task = asyncio.create_task(_bot_loop())
    log.info("Bot task created.")


async def stop_bot():
    global _task
    if not _status.running:
        raise RuntimeError("Bot is not running.")

    _status.running = False
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None

    log.info("Bot stopped by user.")
