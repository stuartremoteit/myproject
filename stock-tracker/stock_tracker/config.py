"""
config.py — Central configuration for the stock tracker.

Override defaults via a .env file (see .env.example).
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Personal watchlist ────────────────────────────────────────────────────────
_env_tickers = os.getenv("TICKERS", "")
DEFAULT_TICKERS: list[str] = (
    [t.strip().upper() for t in _env_tickers.split(",") if t.strip()]
    if _env_tickers
    else ["AAPL", "TSLA", "NVDA"]
)

# ── Market indices — shown as a compact overview above your stock panels ─────
# Keys are Yahoo Finance symbols; values are short display names.
# Add/remove entries here or set MARKET_INDICES=^GSPC,^DJI in .env to override.
_env_indices = os.getenv("MARKET_INDICES", "")
MARKET_INDICES: dict[str, str] = {}
if _env_indices:
    for sym in _env_indices.split(","):
        sym = sym.strip().upper()
        if sym:
            MARKET_INDICES[sym] = sym   # name filled in later from API
else:
    MARKET_INDICES = {
        "^GSPC": "S&P 500",
        "^DJI":  "Dow Jones",
        "^IXIC": "NASDAQ",
        "^RUT":  "Russell 2000",
    }

# ── Ticker → full company name (used for Google News search queries) ───────
COMPANY_NAMES: dict[str, str] = {
    # Stocks
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
    # Indices (used when an index is added to the stock watchlist)
    "^GSPC": "S&P 500",
    "^DJI":  "Dow Jones",
    "^IXIC": "NASDAQ Composite",
    "^RUT":  "Russell 2000",
}

def company_name(ticker: str) -> str:
    """Return the company/index name for a ticker, falling back to the ticker itself."""
    return COMPANY_NAMES.get(ticker.upper(), ticker.upper())

# ── API keys ───────────────────────────────────────────────────────────────
NEWSAPI_KEY: str = os.getenv("NEWSAPI_KEY", "")

# ── Fetch settings ─────────────────────────────────────────────────────────
NEWSAPI_PAGE_SIZE:    int = 5   # headlines per ticker from NewsAPI
YAHOO_MAX_ITEMS:      int = 5   # headlines per ticker from Google News
REQUEST_TIMEOUT:      int = 10  # seconds

# ── Watch / auto-refresh settings ─────────────────────────────────────────
WATCH_INTERVAL_MINUTES: int = int(os.getenv("WATCH_INTERVAL", "30"))
