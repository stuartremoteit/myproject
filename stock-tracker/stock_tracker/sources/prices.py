"""
prices.py — Fetch live price data from Yahoo Finance (no API key needed).

Fetches all tickers in a single HTTP request for efficiency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

from stock_tracker.config import REQUEST_TIMEOUT

# ── Data model ───────────────────────────────────────────────────────────────

@dataclass
class PriceData:
    ticker:       str
    price:        float
    change:       float          # absolute change from previous close
    change_pct:   float          # percentage change
    volume:       Optional[int]
    market_cap:   Optional[float]
    currency:     str
    market_state: str            # REGULAR | PRE | POST | CLOSED | UNKNOWN


# ── Helpers ──────────────────────────────────────────────────────────────────

def fmt_volume(v: Optional[int]) -> str:
    if v is None:
        return "—"
    if v >= 1_000_000_000:
        return f"{v / 1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v / 1_000:.1f}K"
    return str(v)


def fmt_market_cap(mc: Optional[float]) -> str:
    if mc is None:
        return "—"
    if mc >= 1_000_000_000_000:
        return f"${mc / 1_000_000_000_000:.2f}T"
    if mc >= 1_000_000_000:
        return f"${mc / 1_000_000_000:.1f}B"
    if mc >= 1_000_000:
        return f"${mc / 1_000_000:.1f}M"
    return f"${mc:.0f}"


# ── Fetch ─────────────────────────────────────────────────────────────────────

_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_batch(tickers: list[str]) -> dict[str, PriceData]:
    """
    Fetch current price data for every ticker in one HTTP request.

    Returns a dict keyed by uppercase ticker symbol.
    Returns an empty dict on any network / parse error.
    """
    if not tickers:
        return {}
    try:
        resp = requests.get(
            _QUOTE_URL,
            params={"symbols": ",".join(t.upper() for t in tickers)},
            headers=_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        raw_list = resp.json().get("quoteResponse", {}).get("result", [])

        prices: dict[str, PriceData] = {}
        for q in raw_list:
            sym = q.get("symbol", "")
            if not sym:
                continue
            prices[sym] = PriceData(
                ticker=sym,
                price=float(q.get("regularMarketPrice", 0.0)),
                change=float(q.get("regularMarketChange", 0.0)),
                change_pct=float(q.get("regularMarketChangePercent", 0.0)),
                volume=q.get("regularMarketVolume"),
                market_cap=q.get("marketCap"),
                currency=q.get("currency", "USD"),
                market_state=q.get("marketState", "UNKNOWN"),
            )
        return prices

    except Exception:
        return {}
