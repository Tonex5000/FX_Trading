from fastapi import APIRouter
from models.schemas import NewsData
from services.news import fetch_news_data

router = APIRouter(prefix="/api", tags=["News"])


@router.get("/news", response_model=NewsData, summary="ForexFactory economic calendar")
async def get_news():
    """
    Fetches USD and CHF economic events from ForexFactory for the next 24 hours.
    Returns:
    - Aggregate risk level (clear / caution / window_block / hard_block / snb_block)
    - List of upcoming events with impact, timing, and block status
    - SNB event detection (Swiss National Bank — highest risk)
    """
    return await fetch_news_data()
