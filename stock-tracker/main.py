#!/usr/bin/env python3
"""
main.py — Entry point for the Stock News Tracker.

Usage:
    python main.py                           # overview + default watchlist
    python main.py AAPL TSLA                 # specific tickers
    python main.py --no-markets              # skip the market overview
    python main.py --watch                   # auto-refresh every 30 min
    python main.py --watch --interval 5      # auto-refresh every 5 min
    python main.py NVDA --watch -i 10        # specific ticker, 10-min refresh
"""

import argparse
import sys

from stock_tracker import config
from stock_tracker.tracker import run, watch


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stock-tracker",
        description="Live stock news + prices with a market overview dashboard.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python main.py\n"
            "  python main.py AAPL MSFT GOOGL\n"
            "  python main.py --no-markets\n"
            "  python main.py --watch\n"
            "  python main.py TSLA --watch --interval 5\n"
        ),
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        metavar="TICKER",
        help=f"Stock tickers to track. Defaults to: {', '.join(config.DEFAULT_TICKERS)}",
    )
    parser.add_argument(
        "-w", "--watch",
        action="store_true",
        help="Auto-refresh mode: keep running and refresh on a timer.",
    )
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=config.WATCH_INTERVAL_MINUTES,
        metavar="MINUTES",
        help=f"Refresh interval for --watch mode (default: {config.WATCH_INTERVAL_MINUTES}).",
    )
    parser.add_argument(
        "--no-markets",
        action="store_true",
        help="Skip the market overview panel (S&P 500, Dow, NASDAQ, Russell).",
    )
    return parser


def main() -> None:
    args         = _build_parser().parse_args()
    tickers      = [t.upper() for t in args.tickers] if args.tickers else None
    show_markets = not args.no_markets

    try:
        if args.watch:
            watch(tickers, interval_minutes=args.interval,
                  show_markets=show_markets)
        else:
            run(tickers, show_markets=show_markets)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
