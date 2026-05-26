"""
alerts.py — Price alert parsing, checking and edge-triggered state.

Set alerts in .env:
    ALERTS=AAPL>200,TSLA<250,NVDA>900

Syntax:
    TICKER>PRICE   — alert when price rises AT OR ABOVE threshold
    TICKER<PRICE   — alert when price falls AT OR BELOW threshold

Multiple alerts are comma-separated. Alerts are edge-triggered:
they fire once when the condition first becomes true, then re-arm
automatically once the price moves back past the threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stock_tracker.sources.prices import PriceData


# ── Data model ──────────────────────────────────────────────────────────────

@dataclass
class Alert:
    ticker:    str
    direction: str    # "above" | "below"
    threshold: float

    def label(self) -> str:
        op = ">" if self.direction == "above" else "<"
        return f"{self.ticker} {op} ${self.threshold:,.2f}"


@dataclass
class TriggeredAlert:
    alert:         Alert
    current_price: float


# ── State ───────────────────────────────────────────────────────────────────

_fired: set[str] = set()


def _key(a: Alert) -> str:
    return f"{a.ticker}_{a.direction}_{a.threshold}"


# ── Public API ──────────────────────────────────────────────────────────────

def parse(raw: str) -> list[Alert]:
    """
    Parse a comma-separated alert string.

    Example: "AAPL>200,TSLA<250,NVDA>900"
    Silently skips malformed entries.
    """
    result: list[Alert] = []
    for part in raw.split(","):
        part = part.strip().upper()
        if not part:
            continue
        try:
            if ">" in part:
                ticker, threshold = part.split(">", 1)
                result.append(Alert(ticker.strip(), "above", float(threshold.strip())))
            elif "<" in part:
                ticker, threshold = part.split("<", 1)
                result.append(Alert(ticker.strip(), "below", float(threshold.strip())))
        except (ValueError, IndexError):
            pass
    return result


def check(
    alerts: list[Alert],
    prices: dict[str, "PriceData"],
) -> list[TriggeredAlert]:
    """
    Return any alerts that have *newly* triggered since the last call.

    Edge-triggered logic:
    - Fires once when condition becomes true (not yet in _fired set).
    - Re-arms when price moves back past the threshold (_fired key removed).
    """
    triggered: list[TriggeredAlert] = []

    for alert in alerts:
        p = prices.get(alert.ticker)
        if p is None or p.price == 0.0:
            continue

        k   = _key(alert)
        met = (
            alert.direction == "above" and p.price >= alert.threshold
        ) or (
            alert.direction == "below" and p.price <= alert.threshold
        )

        if met and k not in _fired:
            _fired.add(k)
            triggered.append(TriggeredAlert(alert, p.price))
        elif not met:
            _fired.discard(k)

    return triggered
