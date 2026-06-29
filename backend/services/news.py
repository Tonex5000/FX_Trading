"""
ForexFactory Economic Calendar Service.
Fetches upcoming USD and CHF news events, detects SNB risk,
and returns a structured risk assessment for the AI.
"""
from datetime import datetime, timezone, timedelta
import httpx
from models.schemas import NewsData, NewsEvent, NewsRisk

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

IMPACT_RANK = {"High": 3, "Medium": 2, "Low": 1, "Holiday": 0}

SNB_KEYWORDS = [
    "snb", "swiss national bank", "jordan", "schlegel",
    "sight deposits", "swiss interest rate", "swiss rate decision",
]


def _is_snb(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in SNB_KEYWORDS)


def _parse_event(ev: dict) -> NewsEvent | None:
    currency = (ev.get("country") or "").upper()
    if currency not in ("USD", "CHF"):
        return None

    try:
        event_time = datetime.fromisoformat(ev["date"].replace("Z", "+00:00"))
    except (KeyError, ValueError):
        return None

    now       = datetime.now(timezone.utc)
    mins_away = int((event_time - now).total_seconds() / 60)

    # Only events within the next 24h or past 30 min
    if mins_away < -30 or mins_away > 1440:
        return None

    impact        = ev.get("impact", "Low")
    is_high       = IMPACT_RANK.get(impact, 0) >= 3
    is_medium     = IMPACT_RANK.get(impact, 0) == 2
    is_snb_event  = _is_snb(ev.get("title", ""))

    # Determine block status
    if is_snb_event:
        block = "snb_block"
    elif is_high:
        block = "hard_block"
    elif -30 <= mins_away <= 30:
        block = "window_block"
    elif is_medium:
        block = "caution"
    else:
        block = "clear"

    return NewsEvent(
        id            = f"{ev.get('title','')}-{ev.get('date','')}",
        title         = ev.get("title", "Unknown"),
        currency      = currency,
        impact        = impact,
        impact_rank   = IMPACT_RANK.get(impact, 0),
        event_time    = event_time,
        mins_away     = mins_away,
        is_snb        = is_snb_event,
        is_high_impact= is_high,
        block_status  = block,
        forecast      = ev.get("forecast") or None,
        previous      = ev.get("previous") or None,
    )


def _aggregate_risk(events: list[NewsEvent]) -> NewsRisk:
    if not events:
        return NewsRisk(level="clear", label="✓ No EUR/CHF events in next 24h")

    if any(e.block_status == "snb_block"    for e in events):
        return NewsRisk(level="snb_block",   label="🚫 SNB event — absolute block, no trades")
    if any(e.block_status == "hard_block"   for e in events):
        return NewsRisk(level="hard_block",  label="🚫 High-impact news — hard block")
    if any(e.block_status == "window_block" for e in events):
        return NewsRisk(level="window_block",label="⚠ News within 30-min window — blocked")
    if any(e.block_status == "caution"      for e in events):
        return NewsRisk(level="caution",     label="⚠ Medium-impact news — reduce size")
    return NewsRisk(level="clear",           label="✓ News window clear")


async def fetch_news_data() -> NewsData:
    """Fetch ForexFactory calendar and return structured NewsData."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(FF_URL)
            resp.raise_for_status()
            raw = resp.json()

        events = [e for ev in raw if (e := _parse_event(ev)) is not None]
        events.sort(key=lambda e: e.mins_away)
        risk = _aggregate_risk(events)

        return NewsData(
            risk       = risk,
            events     = events,
            fetched_at = datetime.now(timezone.utc),
            source     = "ForexFactory",
        )

    except Exception as exc:
        # Return safe fallback — app keeps running
        return NewsData(
            risk       = NewsRisk(level="unknown", label="⚠ News feed unavailable — trade with caution"),
            events     = [],
            fetched_at = datetime.now(timezone.utc),
            error      = str(exc),
        )
