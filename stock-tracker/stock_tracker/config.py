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

# ── Market indices ────────────────────────────────────────────────────────
_env_indices = os.getenv("MARKET_INDICES", "")
MARKET_INDICES: dict[str, str] = {}
if _env_indices:
    for _sym in _env_indices.split(","):
        _sym = _sym.strip().upper()
        if _sym:
            MARKET_INDICES[_sym] = _sym
else:
    MARKET_INDICES = {
        "^GSPC": "S&P 500",
        "^DJI":  "Dow Jones",
        "^IXIC": "NASDAQ",
        "^RUT":  "Russell 2000",
    }

# ── Sector ETFs ─────────────────────────────────────────────────────────────
SECTOR_ETFS: dict[str, str] = {
    "XLK":  "Technology",
    "XLF":  "Financials",
    "XLE":  "Energy",
    "XLV":  "Health Care",
    "XLI":  "Industrials",
    "XLC":  "Comm. Services",
    "XLY":  "Cons. Discret.",
    "XLP":  "Cons. Staples",
    "XLRE": "Real Estate",
    "XLU":  "Utilities",
    "XLB":  "Materials",
}

# ── Price alerts ─────────────────────────────────────────────────────────────
ALERTS_RAW: str = os.getenv("ALERTS", "")

# ── Ticker → company name ───────────────────────────────────────────────────────
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
    "^GSPC": "S&P 500",
    "^DJI":  "Dow Jones",
    "^IXIC": "NASDAQ Composite",
    "^RUT":  "Russell 2000",
}

def company_name(ticker: str) -> str:
    return COMPANY_NAMES.get(ticker.upper(), ticker.upper())

# ── API keys ───────────────────────────────────────────────────────────────
NEWSAPI_KEY: str = os.getenv("NEWSAPI_KEY", "")

# ── Fetch settings ─────────────────────────────────────────────────────────
NEWSAPI_PAGE_SIZE:    int = 5
YAHOO_MAX_ITEMS:      int = 5
REQUEST_TIMEOUT:      int = 10

# ── Watch / auto-refresh ─────────────────────────────────────────────────────
WATCH_INTERVAL_MINUTES: int = int(os.getenv("WATCH_INTERVAL", "30"))
