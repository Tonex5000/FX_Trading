from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

# ── Add to existing schemas.py ─────────────────────────────────────────────
# These are the new models needed by the trading bot.


class TradeOrder(BaseModel):
    """Represents a trade order sent to OANDA."""
    oanda_order_id:   str
    oanda_trade_id:   Optional[str] = None
    instrument:       str = "USD_CHF"
    side:             Literal["BUY", "SELL"]
    units:            float                    # positive = BUY, negative = SELL
    entry_price:      float
    stop_loss:        float
    take_profit_1:    float
    take_profit_2:    Optional[float] = None
    risk_percent:     float
    risk_amount_usd:  float
    position_size_lots: float
    placed_at:        datetime
    status:           Literal["OPEN", "CLOSED", "CANCELLED", "REJECTED"] = "OPEN"
    close_price:      Optional[float] = None
    close_reason:     Optional[str]   = None   # TP1 / TP2 / SL / MANUAL
    pnl:              Optional[float] = None
    closed_at:        Optional[datetime] = None


class BotRunResult(BaseModel):
    """Result of a single bot cycle."""
    run_id:       str
    started_at:   datetime
    signal:       str                          # BUY / SELL / NO TRADE
    confidence:   int
    filters:      int
    action:       Literal[
        "ORDER_PLACED",      # trade sent to OANDA
        "NO_TRADE",          # AI said no trade
        "SKIPPED_LOW_CONF",  # confidence below threshold
        "SKIPPED_OPEN_TRADE",# already have an open position
        "ERROR_MARKET",      # OANDA fetch failed
        "ERROR_NEWS",        # ForexFactory failed (safe fallback used)
        "ERROR_AI",          # Groq failed
        "ERROR_ORDER",       # OANDA order placement failed
    ]
    order:        Optional[TradeOrder] = None
    message:      str
    completed_at: datetime


class BotConfig(BaseModel):
    """Runtime configuration for the bot."""
    account_balance:     float  = Field(default=10000.0, gt=0)
    min_confidence:      int    = Field(default=70, ge=60, le=95,
                                        description="Minimum AI confidence to place a trade")
    min_filters:         int    = Field(default=7,  ge=5,  le=9,
                                        description="Minimum confluence filters to pass")
    allow_one_trade:     bool   = Field(default=True,
                                        description="Skip new signals if a trade is already open")
    scan_interval_secs:  int    = Field(default=300, ge=60,
                                        description="How often the bot scans in seconds (default 5 min)")
    enabled:             bool   = Field(default=True)


class BotStatus(BaseModel):
    """Live status of the running bot."""
    running:        bool
    config:         BotConfig
    last_run:       Optional[BotRunResult] = None
    open_trade:     Optional[TradeOrder]   = None
    total_runs:     int = 0
    trades_placed:  int = 0
    started_at:     Optional[datetime] = None
