"""
tracker.py — Orchestrates fetching from all sources and deduplicates results.
"""

from __future__ import annotations

import time
from typing import List

from stock_tracker import config, display
from stock_tracker.sources import google_news, newsapi
from stock_tracker.sources.google_news import Article
from stock_tracker.sources.prices import fetch_batch


# ── Helpers ──────────────────────────────────────────────────────────────────

def _deduplicate(articles: List[Article]) -> List[Article]:
    seen:   set[str]      = set()
    unique: List[Article] = []
    for art in articles:
        key = art.title.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(art)
    return unique


def _sort(articles: List[Article]) -> List[Article]:
    return sorted(
        articles,
        key=lambda a: a.published.timestamp() if a.published else 0,
        reverse=True,
    )


# ── Core run ────────────────────────────────────────────────────────────────

def run(tickers: list[str] | None = None,
        watch_mode:       bool = False,
        interval_minutes: int  = config.WATCH_INTERVAL_MINUTES,
        show_markets:     bool = True) -> None:
    tickers = tickers or config.DEFAULT_TICKERS
    start   = time.monotonic()
    total   = 0

    display.print_header(tickers, watch_mode=watch_mode,
                         interval_minutes=interval_minutes)

    if not config.NEWSAPI_KEY:
        display.print_no_key_warning()

    all_symbols = list(config.MARKET_INDICES.keys()) + tickers
    prices = fetch_batch(all_symbols) if show_markets else fetch_batch(tickers)

    if show_markets and config.MARKET_INDICES:
        display.print_market_overview(config.MARKET_INDICES, prices)

    for ticker in tickers:
        company  = config.company_name(ticker)
        articles: List[Article] = []

        articles += google_news.fetch(ticker, company)

        try:
            articles += newsapi.fetch(ticker, company)
        except RuntimeError as exc:
            display.print_error(str(exc))

        articles = _sort(_deduplicate(articles))
        total   += len(articles)

        display.print_ticker_news(ticker, articles, price=prices.get(ticker))

    display.print_summary(total, time.monotonic() - start)


# ── Watch / auto-refresh loop ───────────────────────────────────────────────────

def watch(tickers:          list[str] | None = None,
         interval_minutes: int              = config.WATCH_INTERVAL_MINUTES,
         show_markets:     bool             = True) -> None:
    tickers          = tickers or config.DEFAULT_TICKERS
    interval_seconds = interval_minutes * 60

    try:
        while True:
            display.console.clear()
            run(tickers, watch_mode=True,
                interval_minutes=interval_minutes,
                show_markets=show_markets)

            for remaining in range(interval_seconds, 0, -1):
                display.print_countdown(remaining)
                time.sleep(1)

            display.clear_countdown()

    except KeyboardInterrupt:
        display.clear_countdown()
        display.console.print("\n[dim]Watch mode stopped.[/dim]\n")
