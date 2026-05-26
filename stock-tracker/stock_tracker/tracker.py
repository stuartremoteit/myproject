"""
tracker.py — Orchestrates fetching from all sources and deduplicates results.
"""

from __future__ import annotations

import time
from typing import List

from stock_tracker import config
from stock_tracker.sources import yahoo, newsapi
from stock_tracker.sources.yahoo import Article
from stock_tracker import display


def _deduplicate(articles: List[Article]) -> List[Article]:
    """Remove duplicate headlines (same title, case-insensitive)."""
    seen: set[str] = set()
    unique: List[Article] = []
    for art in articles:
        key = art.title.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(art)
    return unique


def _sort(articles: List[Article]) -> List[Article]:
    """Most-recent first; articles without a date go to the end."""
    return sorted(
        articles,
        key=lambda a: a.published.timestamp() if a.published else 0,
        reverse=True,
    )


def run(tickers: list[str] | None = None) -> None:
    """
    Fetch and display news for every ticker in *tickers*.
    Falls back to config.DEFAULT_TICKERS when None.
    """
    tickers = tickers or config.DEFAULT_TICKERS
    start   = time.monotonic()
    total   = 0

    display.print_header(tickers)

    if not config.NEWSAPI_KEY:
        display.print_no_key_warning()

    for ticker in tickers:
        company  = config.company_name(ticker)
        articles: List[Article] = []

        # ── Yahoo Finance RSS ──────────────────────────────────────────────
        articles += yahoo.fetch(ticker)

        # ── NewsAPI.org ────────────────────────────────────────────────────
        try:
            articles += newsapi.fetch(ticker, company)
        except RuntimeError as exc:
            display.print_error(str(exc))

        articles = _sort(_deduplicate(articles))
        total   += len(articles)

        display.print_ticker_news(ticker, articles)

    display.print_summary(total, time.monotonic() - start)
