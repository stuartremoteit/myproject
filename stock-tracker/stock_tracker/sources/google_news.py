"""
google_news.py — Fetch stock news from Google News RSS.

No API key required. No extra packages — uses requests + stdlib XML.

Search URL format:
  https://news.google.com/rss/search?q=AAPL+Apple+stock&hl=en-US&gl=US&ceid=US:en
"""

from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List

import requests

from stock_tracker.config import YAHOO_MAX_ITEMS, REQUEST_TIMEOUT


# ── Data model (shared across all news sources) ──────────────────────────

@dataclass
class Article:
    ticker:    str
    title:     str
    url:       str
    source:    str
    published: datetime | None


# ── Internals ─────────────────────────────────────────────────────────────

_RSS_BASE = "https://news.google.com/rss/search"
_HEADERS  = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _rss_url(ticker: str, company: str) -> str:
    query = f"{ticker} {company} stock"
    return (
        f"{_RSS_BASE}"
        f"?q={urllib.parse.quote(query)}"
        f"&hl=en-US&gl=US&ceid=US:en"
    )


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str.strip())
    except Exception:
        return None


def _clean_title(title: str, source_name: str) -> str:
    """
    Google News appends ' - Source Name' to every headline title.
    Strip it so we don't duplicate the source in the display.
    """
    title = title.strip()
    suffix = f" - {source_name}"
    if source_name and title.endswith(suffix):
        title = title[: -len(suffix)].strip()
    return title or "(no title)"


# ── Public API ─────────────────────────────────────────────────────────────

def fetch(ticker: str, company: str) -> List[Article]:
    """
    Return up to YAHOO_MAX_ITEMS recent news articles for *ticker*
    from Google News RSS.

    Returns an empty list on any network / parse error so the caller
    can gracefully degrade.
    """
    url = _rss_url(ticker, company)
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        root    = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            return []

        articles: List[Article] = []
        for item in channel.findall("item")[:YAHOO_MAX_ITEMS]:
            source_el   = item.find("source")
            source_name = (source_el.text or "Google News").strip() if source_el is not None else "Google News"

            raw_title = (item.findtext("title") or "").strip()
            title     = _clean_title(raw_title, source_name)
            link      = (item.findtext("link")  or "").strip()
            pub_raw   = item.findtext("pubDate")

            articles.append(
                Article(
                    ticker=ticker.upper(),
                    title=title,
                    url=link,
                    source=source_name,
                    published=_parse_date(pub_raw),
                )
            )
        return articles

    except Exception:
        return []
