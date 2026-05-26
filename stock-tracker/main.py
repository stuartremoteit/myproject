#!/usr/bin/env python3
"""
main.py — Entry point for the Stock News Tracker.

Usage:
    python main.py                          # one-shot: default watchlist
    python main.py AAPL TSLA               # one-shot: specific tickers
    python main.py --watch                 # auto-refresh every 30 min
    python main.py --watch --interval 5    # auto-refresh every 5 min
    python main.py NVDA AMD --watch -i 10  # specific tickers, refresh every 10 min
"""

import argparse
import sys

from stock_tracker import config
from stock_tracker.tracker import run, watch


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stock-tracker",
        description="Ping yourself with the latest news + prices for your stock watchlist.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python main.py\n"
            "  python main.py AAPL MSFT GOOGL\n"
            "  python main.py --watch\n"
            "  python main.py TSLA --watch --interval 5\n"
        ),
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        metavar="TICKER",
        help="Stock tickers to track (e.g. AAPL TSLA). "
             f"Defaults to: {', '.join(config.DEFAULT_TICKERS)}",
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
        help=f"Refresh interval in minutes for --watch mode "
             f"(default: {config.WATCH_INTERVAL_MINUTES}).",
    )
    return parser


def main() -> None:
    args    = _build_parser().parse_args()
    tickers = [t.upper() for t in args.tickers] if args.tickers else None

    try:
        if args.watch:
            watch(tickers, interval_minutes=args.interval)
        else:
            run(tickers)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
