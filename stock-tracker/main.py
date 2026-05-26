#!/usr/bin/env python3
"""
main.py — Entry point for the Stock News Tracker.

Usage:
    python main.py                          # fetch news for all default tickers
    python main.py AAPL TSLA               # fetch news for specific tickers
    python main.py --help
"""

import argparse
import sys

from stock_tracker.tracker import run


def _parse_args() -> list[str] | None:
    parser = argparse.ArgumentParser(
        prog="stock-tracker",
        description="Ping yourself with the latest news for your stock watchlist.",
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        metavar="TICKER",
        help="One or more stock tickers (e.g. AAPL TSLA). "
             "Defaults to your configured watchlist.",
    )
    args = parser.parse_args()
    return [t.upper() for t in args.tickers] if args.tickers else None


def main() -> None:
    tickers = _parse_args()
    try:
        run(tickers)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
