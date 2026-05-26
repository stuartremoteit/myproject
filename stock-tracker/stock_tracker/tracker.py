"""
tracker.py — Orchestrates fetching from all sources and deduplicates results.
"""

from __future__ import annotations

import time
from typing import List

from stock_tracker import config, display
from stock_tracker.sources import yahoo, newsapi
from stock_tracker.sources.prices import fetch_batch
from stock_tracker.sources.yahoo import Article


# ── Helpers ──────────────────────────────────────────────────────────────────

def _deduplicate(articles: List[Article]) -> List[Article]:
    """Remove duplicate headlines (same title, case-insensitive)."""
    seen:   set[str]      = set()
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


# ── Core run ────────────────────────────────────────────────────────────────

def run(tickers: list[str] | None = None,
        watch_mode: bool = False,
        interval_minutes: int = config.WATCH_INTERVAL_MINUTES) -> None:
    """
    Fetch prices + news for every ticker and render to the terminal.
    Falls back to config.DEFAULT_TICKERS when *tickers* is None.
    """
    tickers = tickers or config.DEFAULT_TICKERS
    start   = time.monotonic()
    total   = 0

    display.print_header(tickers, watch_mode=watch_mode,
                         interval_minutes=interval_minutes)

    if not config.NEWSAPI_KEY:
        display.print_no_key_warning()

    # ── Fetch all prices in one round-trip ──────────────────────────────────
    prices = fetch_batch(tickers)

    for ticker in tickers:
        company  = config.company_name(ticker)
        articles: List[Article] = []

        # Yahoo Finance RSS ──────────────────────────────────────────────
        articles += yahoo.fetch(ticker)

        # NewsAPI.org ───────────────────────────────────────────────────
        try:
            articles += newsapi.fetch(ticker, company)
        except RuntimeError as exc:
            display.print_error(str(exc))

        articles = _sort(_deduplicate(articles))
        total   += len(articles)

        display.print_ticker_news(
            ticker,
            articles,
            price=prices.get(ticker),
        )

    display.print_summary(total, time.monotonic() - start)


# ── Watch / auto-refresh loop ───────────────────────────────────────────────────

def watch(tickers: list[str] | None = None,
         interval_minutes: int = config.WATCH_INTERVAL_MINUTES) -> None:
    """
    Continuously refresh news + prices every *interval_minutes* minutes.
    Press Ctrl+C to stop.
    """
    tickers          = tickers or config.DEFAULT_TICKERS
    interval_seconds = interval_minutes * 60

    try:
        while True:
            display.console.clear()
            run(tickers, watch_mode=True, interval_minutes=interval_minutes)

            # ── countdown ───────────────────────────────────────────────────
            for remaining in range(interval_seconds, 0, -1):
                display.print_countdown(remaining)
                time.sleep(1)

            display.clear_countdown()

    except KeyboardInterrupt:
        display.clear_countdown()
        display.console.print("\n[dim]Watch mode stopped.[/dim]\n")
