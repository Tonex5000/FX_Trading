# EUR/CHF AI Trading System 🤖

Full-stack automated FX trading signal engine.  
**Broker:** Pepperstone (accepts Nigerian traders ✓) via cTrader Open API  
**Pair:** EUR/CHF  
**Backend:** Python FastAPI · **Frontend:** React + Vite  
**AI:** Groq — qwen/qwen3-32b · **News:** ForexFactory  
**Fallback:** Twelve Data (auto-activates if Pepperstone data fails)

---

## Architecture

```
Browser (React)
    │
    │  HTTP/JSON
    ▼
FastAPI Backend (Python)
    ├── /api/market    → Pepperstone cTrader (live EUR/CHF price + indicators)
    │                     └── [FALLBACK] Twelve Data if Pepperstone fails
    ├── /api/news      → ForexFactory (upcoming EUR/CHF news + SNB events)
    ├── /api/analyze   → Groq AI (qwen3-32b) makes final trade decision
    └── /api/bot/*     → Automated trading bot (runs every 5 min)
                          └── Places trades on Pepperstone via cTrader Open API
```

---

## Project Structure

```
fx-trading-ai/
├── frontend/          React + Vite UI
│   └── src/
│       ├── components/   Header, MarketSnapshot, NewsPanel, SignalResult, BotPanel, Journal
│       ├── hooks/        useAnalysis, useJournal
│       └── services/     api.js (all calls go to FastAPI — no direct broker calls)
│
└── backend/           Python FastAPI server
    ├── core/          config.py (all env vars)
    ├── models/        schemas.py (Pydantic models)
    ├── services/
    │   ├── pepperstone.py   ← PRIMARY broker (market data + trade execution)
    │   ├── twelvedata.py    ← FALLBACK market data (auto-used if Pepperstone fails)
    │   ├── news.py          ← ForexFactory economic calendar
    │   ├── groq.py          ← AI decision engine (qwen/qwen3-32b)
    │   └── indicators.py    ← ADX, ATR, EMA calculations (pure Python)
    ├── routers/
    │   ├── market.py        GET /api/market
    │   ├── news.py          GET /api/news
    │   ├── analysis.py      POST /api/analyze
    │   └── bot.py           /api/bot/* (start/stop/status/history)
    └── bot/
        ├── engine.py        ← Main bot loop (runs every 5 min)
        ├── executor.py      ← Delegates trade execution to pepperstone.py
        └── schemas.py       ← BotConfig, BotStatus, TradeOrder, BotRunResult
```

---

## Why Pepperstone?

Pepperstone is fully available to Nigerian traders as of 2026 — unlike OANDA which does not accept Nigerian clients.

- Regulated by FCA (UK), ASIC (Australia), CySEC — Nigerian traders are onboarded under Pepperstone Bahamas (SCB regulated)
- Accepts Visa/Mastercard, Skrill, Neteller, bank transfer
- Minimum deposit: $200
- Full access to MT4, MT5, cTrader, and TradingView platforms
- cTrader Open API enables programmatic trading

---

## Quick Start

### 1. Clone
```bash
git clone https://github.com/YOUR_USERNAME/fx-trading-ai.git
cd fx-trading-ai
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — add your API keys (see below)
uvicorn main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
# .env.local: VITE_API_URL=http://localhost:8000
npm run dev
```

---

## API Keys Needed

| # | Service | Cost | Purpose |
|---|---------|------|---------|
| 1 | **Groq** | Free | AI decisions — https://console.groq.com |
| 2 | **Pepperstone cTrader** | Free (with account) | Live EUR/CHF data + trade execution |
| 3 | **Twelve Data** | Free (800 calls/day) | Fallback data if Pepperstone fails |
| 4 | **ForexFactory** | Free, no key needed | Economic calendar |

### Getting Pepperstone cTrader API credentials
1. Open account at https://www.pepperstone.com (Nigerian traders: select Bahamas entity)
2. Go to https://openapi.ctrader.com → Create Application
3. Copy `client_id` and `client_secret`
4. Get your `access_token` via OAuth2
5. Find your `account_id` in the cTrader portal

### Getting Twelve Data API key (fallback)
1. Go to https://twelvedata.com → Sign up free
2. Copy your API key
3. Free tier: 800 calls/day (more than enough)

---

## Bot Safety Features

- Minimum 70% AI confidence required to place a trade
- Minimum 7/9 confluence filters must pass
- One trade at a time — no stacking positions
- Emergency close button in the UI
- Full run history logged with every cycle

---

## ⚠️ Disclaimer
Educational and research use only. Not financial advice.  
Always test on a Pepperstone demo account before live trading.
