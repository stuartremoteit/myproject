"""
newsapi.py — Fetch stock news from NewsAPI.org.

Requires a free API key: https://newsapi.org/register
Set NEWSAPI_KEY in your .env file.
"""

from __future__ import annotations

import requests
from datetime import datetime
from typing import List

from stock_tracker.config import NEWSAPI_KEY, NEWSAPI_PAGE_SIZE, REQUEST_TIMEOUT
from stock_tracker.sources.google_news import Article  # shared Article dataclass


_ENDPOINT = "https://newsapi.org/v2/everything"


def _parse_date(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        return None


def fetch(ticker: str, company: str) -> List[Article]:
    """
    Return up to NEWSAPI_PAGE_SIZE articles mentioning *ticker* or *company*.

    Returns an empty list when:
    - NEWSAPI_KEY is not configured
    - The request fails or returns an error status
    """
    if not NEWSAPI_KEY:
        return []

    params = {
        "q":        f'"{ticker}" OR "{company}"',
        "apiKey":   NEWSAPI_KEY,
        "pageSize": NEWSAPI_PAGE_SIZE,
        "sortBy":   "publishedAt",
        "language": "en",
    }

    try:
        resp = requests.get(_ENDPOINT, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        articles: List[Article] = []
        for item in data.get("articles", []):
            articles.append(
                Article(
                    ticker=ticker.upper(),
                    title=(item.get("title") or "(no title)").strip(),
                    url=item.get("url", ""),
                    source=item.get("source", {}).get("name", "NewsAPI"),
                    published=_parse_date(item.get("publishedAt")),
                )
            )
        return articles

    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 401:
            raise RuntimeError(
                "NewsAPI returned 401 Unauthorized — check your NEWSAPI_KEY in .env"
            ) from exc
        return []
    except Exception:
        return []
