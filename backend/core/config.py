from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Groq AI ───────────────────────────────────────────────
    groq_api_key: str

    # ── Pepperstone cTrader Open API ──────────────────────────
    # Register your app at: https://openapi.ctrader.com
    ctrader_client_id:     str = ""
    ctrader_client_secret: str = ""
    ctrader_access_token:  str = ""          # OAuth2 access token
    ctrader_account_id:    str = ""          # optional — auto-fetched if blank

    # ── Twelve Data (fallback market data) ────────────────────
    # Free tier (800 calls/day): https://twelvedata.com
    twelve_data_api_key: str = "demo"        # 'demo' works for basic testing

    # ── App ───────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
