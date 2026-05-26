"""
config.py — Central configuration for the stock tracker.

Override defaults via a .env file (see .env.example).
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Watchlist ──────────────────────────────────────────────────────────────
_env_tickers = os.getenv("TICKERS", "")
DEFAULT_TICKERS: list[str] = (
    [t.strip().upper() for t in _env_tickers.split(",") if t.strip()]
    if _env_tickers
    else ["AAPL", "TSLA", "NVDA"]
)

# ── Ticker → full company name (used for NewsAPI search queries) ───────────
COMPANY_NAMES: dict[str, str] = {
    "AAPL":  "Apple",
    "TSLA":  "Tesla",
    "NVDA":  "Nvidia",
    "GOOGL": "Google Alphabet",
    "MSFT":  "Microsoft",
    "AMZN":  "Amazon",
    "META":  "Meta Platforms",
    "NFLX":  "Netflix",
    "AMD":   "AMD semiconductor",
    "INTC":  "Intel",
    "BABA":  "Alibaba",
    "JPM":   "JPMorgan Chase",
    "BAC":   "Bank of America",
    "GS":    "Goldman Sachs",
    "V":     "Visa",
    "MA":    "Mastercard",
}

def company_name(ticker: str) -> str:
    """Return the company name for a ticker, falling back to the ticker itself."""
    return COMPANY_NAMES.get(ticker.upper(), ticker.upper())

# ── API keys ───────────────────────────────────────────────────────────────
NEWSAPI_KEY: str = os.getenv("NEWSAPI_KEY", "")

# ── Fetch settings ─────────────────────────────────────────────────────────
NEWSAPI_PAGE_SIZE:    int = 5   # headlines per ticker from NewsAPI
YAHOO_MAX_ITEMS:      int = 5   # headlines per ticker from Yahoo RSS
REQUEST_TIMEOUT:      int = 10  # seconds

# ── Watch / auto-refresh settings ─────────────────────────────────────────
WATCH_INTERVAL_MINUTES: int = int(os.getenv("WATCH_INTERVAL", "30"))
