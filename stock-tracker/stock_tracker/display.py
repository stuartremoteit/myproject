"""
display.py — Rich terminal rendering for stock news.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from stock_tracker.sources.yahoo import Article

console = Console()


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


def print_header(tickers: list[str]) -> None:
    """Print a startup banner."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(
        Panel(
            f"[bold cyan]📈 Stock News Tracker[/bold cyan]\n"
            f"[dim]Watching: [bold]{', '.join(tickers)}[/bold]   |   {ts}[/dim]",
            box=box.DOUBLE_EDGE,
            border_style="cyan",
            padding=(0, 2),
        )
    )


def print_ticker_news(ticker: str, articles: List[Article]) -> None:
    """Render a Rich table of headlines for one ticker."""
    if not articles:
        console.print(f"[yellow]  {ticker}[/yellow]  [dim]— no headlines found[/dim]\n")
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
    table.add_column("Source", style="dim green", no_wrap=True, width=16)
    table.add_column("Headline")

    for art in articles:
        age  = _age(art.published)
        src  = art.source[:15] if art.source else "—"
        link = f"[link={art.url}]{art.title}[/link]" if art.url else art.title
        table.add_row(age, src, link)

    console.print(
        Panel(
            table,
            title=f"[bold white] {ticker} [/bold white]",
            border_style="bright_blue",
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
