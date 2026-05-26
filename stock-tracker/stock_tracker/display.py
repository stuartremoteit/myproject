"""
display.py — Rich terminal rendering for stock news, prices, market overview,
             sector performance and price alerts.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich import box

from stock_tracker.sources.google_news import Article
from stock_tracker.sources.prices import PriceData, fmt_volume, fmt_market_cap

if TYPE_CHECKING:
    from stock_tracker.alerts import TriggeredAlert

console = Console()


# ── Generic helpers ────────────────────────────────────────────────────────────────

def _age(dt: datetime | None) -> str:
    if dt is None:
        return "?"
    seconds = int((datetime.now(tz=timezone.utc) - dt).total_seconds())
    if seconds < 60:    return "just now"
    if seconds < 3600:  return f"{seconds // 60}m ago"
    if seconds < 86400: return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def _direction(change: float) -> tuple[str, str, str]:
    return ("▲", "green", "+") if change >= 0 else ("▼", "red", "")


def _state_label(state: str) -> str:
    return {"PRE": "pre-mkt", "POST": "after-hrs", "CLOSED": "closed"}.get(state, "")


def _fmt_pct(p: Optional[PriceData]) -> str:
    if p is None or p.price == 0.0:
        return "[dim]—[/dim]"
    arrow, colour, sign = _direction(p.change)
    return f"[{colour}]{arrow} {sign}{p.change_pct:.2f}%[/{colour}]"


# ── 52-week range bar ─────────────────────────────────────────────────────────────

def _52w_bar(p: PriceData, bar_width: int = 24) -> Text | None:
    low, high = p.fifty_two_week_low, p.fifty_two_week_high
    if not low or not high or high <= low:
        return None
    pct    = max(0.0, min(1.0, (p.price - low) / (high - low)))
    filled = round(pct * bar_width)
    bar    = "█" * filled + "░" * (bar_width - filled)
    colour = "green" if pct >= 0.67 else "red" if pct <= 0.33 else "yellow"
    t = Text(justify="left")
    t.append("  52w  ", style="dim")
    t.append(f"${low:,.2f}", style="dim")
    t.append("  ▏", style="dim")
    t.append(bar, style=colour)
    t.append("▊  ", style="dim")
    t.append(f"${high:,.2f}", style="dim")
    t.append(f"   {pct * 100:.0f}%", style="bold")
    t.append(" of range", style="dim")
    return t


# ── Panel title / border helpers ───────────────────────────────────────────────────

def _price_title(ticker: str, p: Optional[PriceData]) -> str:
    if p is None or p.price == 0.0:
        return f"[bold white] {ticker} [/bold white][dim] price unavailable[/dim]"
    arrow, colour, sign = _direction(p.change)
    state_tag = f" [dim]{_state_label(p.market_state)}[/dim]" if _state_label(p.market_state) else ""
    return (
        f"[bold white] {ticker} [/bold white]"
        f"[{colour}] {p.currency} {p.price:,.2f}  "
        f"{arrow} {sign}{p.change:+.2f} ({sign}{p.change_pct:.2f}%)[/{colour}]"
        f"  [dim]Vol {fmt_volume(p.volume)}  Cap {fmt_market_cap(p.market_cap)}[/dim]"
        f"{state_tag}"
    )


def _border_colour(p: Optional[PriceData]) -> str:
    if p is None or p.price == 0.0:
        return "bright_blue"
    return "green" if p.change >= 0 else "red"


# ── Price alerts ─────────────────────────────────────────────────────────────

def print_alerts(triggered: list["TriggeredAlert"]) -> None:
    for ta in triggered:
        up        = ta.alert.direction == "above"
        colour    = "green" if up else "red"
        arrow     = "▲" if up else "▼"
        direction = "ABOVE" if up else "BELOW"
        console.print(
            Panel(
                f"  [{colour}]{arrow}[/{colour}]  "
                f"[bold white]{ta.alert.ticker}[/bold white] is now "
                f"[{colour}][bold]${ta.current_price:,.2f}[/bold][/{colour}]"
                f"  —  crossed {direction} target "
                f"[bold]${ta.alert.threshold:,.2f}[/bold]",
                title="[bold]🔔 PRICE ALERT[/bold]",
                border_style=f"bold {colour}",
                padding=(0, 1),
            )
        )
        print("\a", end="", flush=True)


# ── Market overview (indices) ─────────────────────────────────────────────────────

def print_market_overview(
    indices: dict[str, str],
    prices:  dict[str, PriceData],
) -> None:
    table = Table(
        box=box.SIMPLE_HEAD, border_style="dim",
        show_header=True, header_style="bold white", padding=(0, 2),
    )
    table.add_column("Index",  style="bold",    no_wrap=True)
    table.add_column("Price",  justify="right", no_wrap=True)
    table.add_column("Change", justify="right", no_wrap=True)
    table.add_column("%",      justify="right", no_wrap=True)
    table.add_column("",       style="dim",     no_wrap=True, width=9)
    for symbol, name in indices.items():
        p = prices.get(symbol)
        if p is None or p.price == 0.0:
            table.add_row(name, "[dim]—[/dim]", "[dim]—[/dim]", "[dim]—[/dim]", "")
            continue
        arrow, colour, sign = _direction(p.change)
        table.add_row(
            name, f"{p.price:>12,.2f}",
            f"[{colour}]{arrow} {sign}{p.change:.2f}[/{colour}]",
            f"[{colour}]{sign}{p.change_pct:.2f}%[/{colour}]",
            f"[dim]{_state_label(p.market_state)}[/dim]",
        )
    sp     = prices.get("^GSPC")
    border = ("green" if sp.change >= 0 else "red") if (sp and sp.price) else "cyan"
    console.print(Panel(table, title="[bold]\U0001f4ca Market Overview[/bold]",
                        border_style=border, padding=(0, 0)))


# ── Sector performance ─────────────────────────────────────────────────────────────

def print_sector_overview(
    sectors: dict[str, str],
    prices:  dict[str, PriceData],
) -> None:
    items = list(sectors.items())
    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_column("name1", no_wrap=True,    min_width=16)
    table.add_column("pct1",  justify="right", min_width=10, no_wrap=True)
    table.add_column("gap",   width=1)
    table.add_column("name2", no_wrap=True,    min_width=16)
    table.add_column("pct2",  justify="right", min_width=10, no_wrap=True)
    for i in range(0, len(items), 2):
        sym1, name1 = items[i]
        p1          = prices.get(sym1)
        if i + 1 < len(items):
            sym2, name2 = items[i + 1]
            p2 = prices.get(sym2)
        else:
            name2, p2 = "", None
        table.add_row(name1, _fmt_pct(p1), "", name2, _fmt_pct(p2) if name2 else "")
    have   = [prices.get(s) for s in sectors if prices.get(s) and prices[s].price > 0]
    ups    = sum(1 for p in have if p.change >= 0)
    border = "green" if ups > len(have) / 2 else "red" if have else "cyan"
    console.print(Panel(table, title="[bold]\U0001f3ed Sectors[/bold]",
                        border_style=border, padding=(0, 1)))


# ── Banner ──────────────────────────────────────────────────────────────────

def print_header(tickers: list[str], watch_mode: bool = False,
                interval_minutes: int = 30) -> None:
    ts    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    live  = "  [blink bold green]● LIVE[/blink bold green]" if watch_mode else ""
    intvl = f"  [dim]auto-refresh every {interval_minutes}m[/dim]" if watch_mode else ""
    console.print(
        Panel(
            f"[bold cyan]\U0001f4c8 Stock News Tracker[/bold cyan]{live}\n"
            f"[dim]Watching: [bold]{', '.join(tickers)}[/bold]"
            f"   |   {ts}{intvl}[/dim]",
            box=box.DOUBLE_EDGE, border_style="cyan", padding=(0, 2),
        )
    )


# ── Per-ticker panel ─────────────────────────────────────────────────────────────

def print_ticker_news(ticker: str, articles: List[Article],
                      price: Optional[PriceData] = None) -> None:
    title  = _price_title(ticker, price)
    border = _border_colour(price)
    if articles:
        tbl = Table(
            box=box.SIMPLE_HEAD, border_style="dim",
            show_header=True, header_style="bold magenta",
            expand=True, padding=(0, 1),
        )
        tbl.add_column("Age",    style="dim cyan",  no_wrap=True, width=9)
        tbl.add_column("Source", style="dim green", no_wrap=True, width=18)
        tbl.add_column("Headline")
        for art in articles:
            src  = (art.source or "—")[:17]
            link = f"[link={art.url}]{art.title}[/link]" if art.url else art.title
            tbl.add_row(_age(art.published), src, link)
        news_block: object = tbl
    else:
        news_block = Text("no headlines found", style="dim")
    bar     = _52w_bar(price) if price else None
    content = Group(bar, Rule(style="dim"), news_block) if bar else news_block
    console.print(Panel(content, title=title, border_style=border, padding=(0, 0)))


# ── Status / misc ─────────────────────────────────────────────────────────────

def print_no_key_warning() -> None:
    console.print(
        "[yellow]⚠  NEWSAPI_KEY not set — skipping NewsAPI source.\n"
        "   Add it to .env to get a second news feed.[/yellow]\n"
    )
def print_error(msg: str) -> None:
    console.print(f"[bold red]✗ Error:[/bold red] {msg}")
def print_summary(total: int, elapsed: float) -> None:
    console.print(f"\n[dim]─── {total} headline(s) fetched in {elapsed:.1f}s ───[/dim]\n")
def print_countdown(remaining_seconds: int) -> None:
    mins, secs = divmod(remaining_seconds, 60)
    sys.stdout.write(f"\r  ⏱  Next refresh in {mins}:{secs:02d}   Ctrl+C to stop           ")
    sys.stdout.flush()
def clear_countdown() -> None:
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()
