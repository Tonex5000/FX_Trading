from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# ── OANDA / Market ────────────────────────────────────────────────────────

class PriceData(BaseModel):
    bid: float
    ask: float
    mid: float
    spread: float


class SessionInfo(BaseModel):
    id: str
    label: str
    quality: Literal["optimal", "good", "caution", "avoid"]


class MarketData(BaseModel):
    price: PriceData
    adx: int = Field(description="4H ADX (14-period)")
    adx_1h: int = Field(description="1H ADX (14-period)")
    atr: float = Field(description="4H ATR (14-period)")
    atr_1h: float = Field(description="1H ATR (14-period)")
    trend_4h: str = Field(description="4H trend direction")
    trend_1h: str = Field(description="1H trend direction")
    ema_4h: float = Field(description="4H EMA 21 value")
    above_ema_4h: bool
    volatility: Literal["very_low", "low", "medium", "high", "extreme"]
    session: SessionInfo
    fetched_at: datetime


# ── News ─────────────────────────────────────────────────────────────────

class NewsEvent(BaseModel):
    id: str
    title: str
    currency: str
    impact: str
    impact_rank: int
    event_time: datetime
    mins_away: int
    is_snb: bool
    is_high_impact: bool
    block_status: str
    forecast: Optional[str] = None
    previous: Optional[str] = None


class NewsRisk(BaseModel):
    level: str
    label: str


class NewsData(BaseModel):
    risk: NewsRisk
    events: list[NewsEvent]
    fetched_at: datetime
    source: str = "ForexFactory"
    error: Optional[str] = None


# ── AI Signal ────────────────────────────────────────────────────────────

class ConfluenceCheck(BaseModel):
    tf_4h_1h_agree: bool
    ema21_aligned: bool
    adx_regime_valid: bool
    pullback_entry: bool
    session_valid: bool
    news_window_clear: bool
    snb_risk_clear: bool
    stop_within_atr15: bool
    rr_minimum_1to2: bool


class TradeSignal(BaseModel):
    signal: Literal["BUY", "SELL", "NO TRADE"]
    confidence: int = Field(ge=0, le=100)
    market_condition: str
    regime: Literal["TRENDING", "BORDERLINE", "CHOPPY"]
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    stop_basis: Optional[str] = None
    risk_reward: str
    risk_percent: Optional[float] = None
    position_size_lots: Optional[float] = None
    stop_pips: Optional[int] = None
    tp1_pips: Optional[int] = None
    confluence_check: ConfluenceCheck
    filters_passed: int = Field(ge=0, le=9)
    auto_data_quality: Literal["HIGH", "MEDIUM", "LOW"]
    reasoning: str
    trade_plan: str
    blocked_by: Optional[str] = None
    market_context: str
    news_assessment: str
    next_check: str
    warnings: list[str] = []


# ── Request / Response ───────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    account_balance: float = Field(default=10000.0, gt=0, description="Account balance in USD")


class AnalyzeResponse(BaseModel):
    market: MarketData
    news: NewsData
    signal: TradeSignal
    analyzed_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    oanda_env: str
