"""
prices.py — Fetch live price data from Yahoo Finance.

Yahoo Finance has required a session-cookie + crumb token since 2024.
We handle this automatically — no API key or manual setup needed.
The handshake is:
  1. GET https://fc.yahoo.com          → receive session cookies
  2. GET .../v1/test/getcrumb          → exchange cookies for a crumb string
  3. GET .../v7/finance/quote?crumb=…  → actual price data
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

from stock_tracker.config import REQUEST_TIMEOUT

# ── Data model ──────────────────────────────────────────────────────────────

@dataclass
class PriceData:
    ticker:       str
    price:        float
    change:       float        # absolute change vs previous close
    change_pct:   float        # percentage change
    volume:       Optional[int]
    market_cap:   Optional[float]
    currency:     str
    market_state: str          # REGULAR | PRE | POST | CLOSED | UNKNOWN


# ── Format helpers ──────────────────────────────────────────────────────────

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
    if mc >= 1e12:
        return f"${mc / 1e12:.2f}T"
    if mc >= 1e9:
        return f"${mc / 1e9:.1f}B"
    if mc >= 1e6:
        return f"${mc / 1e6:.1f}M"
    return f"${mc:.0f}"


# ── Session / crumb management ──────────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin":          "https://finance.yahoo.com",
    "Referer":         "https://finance.yahoo.com/",
}

_CONSENT_URL = "https://fc.yahoo.com"
_CRUMB_URL   = "https://query2.finance.yahoo.com/v1/test/getcrumb"
_QUOTE_URL   = "https://query1.finance.yahoo.com/v7/finance/quote"

# Cached per-process session and crumb
_session: Optional[requests.Session] = None
_crumb:   str = ""


def _init_session() -> tuple[requests.Session, str]:
    """Create a fresh Yahoo Finance session + crumb. Caches the result."""
    global _session, _crumb

    s = requests.Session()
    s.headers.update(_HEADERS)
    crumb = ""

    try:
        # Touch consent page so Yahoo sets the required session cookies
        s.get(_CONSENT_URL, timeout=REQUEST_TIMEOUT)
        # Exchange those cookies for a crumb token
        r = s.get(_CRUMB_URL, timeout=REQUEST_TIMEOUT)
        if r.ok and r.text.strip() and len(r.text.strip()) < 64:
            crumb = r.text.strip()
    except Exception:
        pass  # proceed without crumb; may still work on some networks

    _session = s
    _crumb   = crumb
    return s, crumb


def _get_session() -> tuple[requests.Session, str]:
    """Return the cached session, creating it on first call."""
    global _session, _crumb
    if _session is None:
        return _init_session()
    return _session, _crumb


def _reset() -> None:
    """Force a new session on the next call (used after 401 errors)."""
    global _session, _crumb
    _session = None
    _crumb   = ""


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_batch(tickers: list[str]) -> dict[str, PriceData]:
    """
    Fetch current price data for all tickers in a single HTTP request.

    Returns a dict keyed by uppercase ticker symbol.
    Returns an empty dict (graceful degradation) on any error.
    """
    if not tickers:
        return {}

    for attempt in range(2):          # try once; retry once after 401
        session, crumb = _get_session()

        params: dict = {"symbols": ",".join(t.upper() for t in tickers)}
        if crumb:
            params["crumb"] = crumb

        try:
            resp = session.get(_QUOTE_URL, params=params, timeout=REQUEST_TIMEOUT)

            if resp.status_code == 401 and attempt == 0:
                # Crumb is stale — reset and retry
                _reset()
                continue

            resp.raise_for_status()
            raw = resp.json().get("quoteResponse", {}).get("result", [])

            prices: dict[str, PriceData] = {}
            for q in raw:
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
            if attempt == 0:
                _reset()
                continue
            return {}

    return {}
