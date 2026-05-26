"""
display.py — Rich terminal rendering for stock news + prices.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from stock_tracker.sources.google_news import Article
from stock_tracker.sources.prices import PriceData, fmt_volume, fmt_market_cap

console = Console()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _age(dt: datetime | None) -> str:
    """Return a human-friendly age string like '2h ago' or 'just now'."""
    if dt is None:
        return "?"
    now = datetime.now(tz=timezone.utc)
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def _price_title(ticker: str, p: Optional[PriceData]) -> str:
    """Build a Rich-markup panel title string with price info."""
    if p is None or p.price == 0.0:
        return f"[bold white] {ticker} [/bold white][dim] price unavailable[/dim]"

    arrow  = "▲" if p.change >= 0 else "▼"
    colour = "green" if p.change >= 0 else "red"
    sign   = "+" if p.change >= 0 else ""

    state_tag = {
        "PRE":    " [dim]pre-market[/dim]",
        "POST":   " [dim]after-hours[/dim]",
        "CLOSED": " [dim]closed[/dim]",
    }.get(p.market_state, "")

    vol  = fmt_volume(p.volume)
    mcap = fmt_market_cap(p.market_cap)

    return (
        f"[bold white] {ticker} [/bold white]"
        f"[{colour}] {p.currency} {p.price:,.2f}  "
        f"{arrow} {sign}{p.change:+.2f} ({sign}{p.change_pct:.2f}%)[/{colour}]"
        f"  [dim]Vol {vol}  Cap {mcap}[/dim]"
        f"{state_tag}"
    )


def _border_colour(p: Optional[PriceData]) -> str:
    if p is None or p.price == 0.0:
        return "bright_blue"
    return "green" if p.change >= 0 else "red"


# ── Public print functions ─────────────────────────────────────────────────────

def print_header(tickers: list[str], watch_mode: bool = False,
                interval_minutes: int = 30) -> None:
    """Print the startup / refresh banner."""
    ts    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    live  = "  [blink bold green]● LIVE[/blink bold green]" if watch_mode else ""
    intvl = (
        f"  [dim]auto-refresh every {interval_minutes}m[/dim]"
        if watch_mode else ""
    )
    console.print(
        Panel(
            f"[bold cyan]\U0001f4c8 Stock News Tracker[/bold cyan]{live}\n"
            f"[dim]Watching: [bold]{', '.join(tickers)}[/bold]"
            f"   |   {ts}{intvl}[/dim]",
            box=box.DOUBLE_EDGE,
            border_style="cyan",
            padding=(0, 2),
        )
    )


def print_ticker_news(ticker: str, articles: List[Article],
                      price: Optional[PriceData] = None) -> None:
    """Render a Rich panel with price info + headlines for one ticker."""

    title  = _price_title(ticker, price)
    border = _border_colour(price)

    if not articles:
        console.print(
            Panel(
                Text("no headlines found", style="dim"),
                title=title,
                border_style=border,
                padding=(0, 1),
            )
        )
        return

    table = Table(
        box=box.SIMPLE_HEAD,
        border_style="dim",
        show_header=True,
        header_style="bold magenta",
        expand=True,
        padding=(0, 1),
    )
    table.add_column("Age",    style="dim cyan",  no_wrap=True, width=9)
    table.add_column("Source", style="dim green", no_wrap=True, width=18)
    table.add_column("Headline")

    for art in articles:
        age  = _age(art.published)
        src  = (art.source or "—")[:17]
        link = f"[link={art.url}]{art.title}[/link]" if art.url else art.title
        table.add_row(age, src, link)

    console.print(
        Panel(
            table,
            title=title,
            border_style=border,
            padding=(0, 0),
        )
    )


def print_no_key_warning() -> None:
    console.print(
        "[yellow]⚠  NEWSAPI_KEY not set — skipping NewsAPI source.\n"
        "   Add it to .env to get a second news feed.[/yellow]\n"
    )


def print_error(msg: str) -> None:
    console.print(f"[bold red]✗ Error:[/bold red] {msg}")


def print_summary(total: int, elapsed: float) -> None:
    console.print(
        f"\n[dim]─── {total} headline(s) fetched in {elapsed:.1f}s ───[/dim]\n"
    )


def print_countdown(remaining_seconds: int) -> None:
    """Overwrite the current line with a countdown timer."""
    mins, secs = divmod(remaining_seconds, 60)
    sys.stdout.write(
        f"\r  ⏱  Next refresh in {mins}:{secs:02d}   "
        "Ctrl+C to stop           "
    )
    sys.stdout.flush()


def clear_countdown() -> None:
    """Erase the countdown line before the next refresh."""
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()
