"""
yahoo.py — Fetch stock news headlines from Yahoo Finance RSS feeds.

Uses only the standard library (xml.etree.ElementTree + requests).
No API key required.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List

import requests

from stock_tracker.config import YAHOO_MAX_ITEMS, REQUEST_TIMEOUT


@dataclass
class Article:
    ticker:    str
    title:     str
    url:       str
    source:    str
    published: datetime | None


_RSS_URL = (
    "https://feeds.finance.yahoo.com/rss/2.0/headline"
    "?s={ticker}&region=US&lang=en-US"
)
_HEADERS = {"User-Agent": "stock-tracker/1.0 (github.com/user/stock-tracker)"}


def _parse_rfc2822(date_str: str | None) -> datetime | None:
    """Parse an RFC-2822 date string (used in RSS pubDate fields)."""
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str.strip())
    except Exception:
        return None


def fetch(ticker: str) -> List[Article]:
    """
    Return up to YAHOO_MAX_ITEMS news articles for *ticker* from Yahoo Finance RSS.

    Returns an empty list on any network / parse error so the caller can
    gracefully degrade.
    """
    url = _RSS_URL.format(ticker=ticker.upper())
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            return []

        articles: List[Article] = []
        for item in channel.findall("item")[:YAHOO_MAX_ITEMS]:
            title   = (item.findtext("title") or "").strip()
            link    = (item.findtext("link")  or "").strip()
            pub_raw = item.findtext("pubDate")
            articles.append(
                Article(
                    ticker=ticker.upper(),
                    title=title or "(no title)",
                    url=link,
                    source="Yahoo Finance",
                    published=_parse_rfc2822(pub_raw),
                )
            )
        return articles

    except Exception:
        return []
