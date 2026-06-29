"""
USD/CHF AI Trading System — FastAPI Backend
==========================================
Runs on: http://localhost:8000
Docs at: http://localhost:8000/docs   (Swagger UI)
         http://localhost:8000/redoc  (ReDoc)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_settings
from models.schemas import HealthResponse
from routers import market, news, analysis, bot

# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "USD/CHF AI Trading System",
    description = "Automated FX signal engine — Pepperstone + ForexFactory + Groq (qwen/qwen3-32b)",
    version     = "2.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────
cfg = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins     = cfg.cors_origins,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(market.router)
app.include_router(news.router)
app.include_router(analysis.router)
app.include_router(bot.router)


# ── Health check ──────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    return HealthResponse(
        status    = "ok",
        version   = "2.0.0",
        oanda_env = cfg.oanda_env,
    )


# ── Dev runner ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
