# 📈 Stock News Tracker

A lightweight CLI tool that pings you with the latest news for your stock watchlist when you activate it.

## Features

- **Two news sources**: Yahoo Finance RSS (no key needed) + NewsAPI.org
- **Beautiful terminal output** using [Rich](https://github.com/Textualize/rich)
- **Deduplicated headlines** sorted most-recent first
- **Configurable watchlist** via `.env` or CLI arguments

## Quick Start

### 1. Install dependencies

```bash
cd stock-tracker
pip install -r requirements.txt
```

### 2. Configure your API key (optional but recommended)

```bash
cp .env.example .env
# Edit .env and add your NewsAPI key
# Free key: https://newsapi.org/register
```

### 3. Run it

```bash
# Fetch news for default watchlist (AAPL, TSLA, NVDA)
python main.py

# Fetch news for specific tickers
python main.py AAPL MSFT GOOGL

# Help
python main.py --help
```

## Configuration

Edit `.env` to customise:

| Variable        | Default            | Description                              |
|----------------|--------------------|-----------------------------------------|
| `NEWSAPI_KEY`  | *(empty)*          | Your free NewsAPI.org key                |
| `TICKERS`      | `AAPL,TSLA,NVDA`   | Comma-separated default watchlist        |

## Adding More Tickers

Add tickers to `TICKERS` in `.env`, or pass them on the command line. For better
NewsAPI search quality, add company name mappings to `COMPANY_NAMES` in
`stock_tracker/config.py`.

## Project Layout

```
stock-tracker/
├── main.py                     ← Entry point
├── requirements.txt
├── .env.example
└── stock_tracker/
    ├── config.py               ← Watchlist, API keys, settings
    ├── display.py              ← Rich terminal rendering
    ├── tracker.py              ← Orchestration & deduplication
    └── sources/
        ├── yahoo.py            ← Yahoo Finance RSS adapter
        └── newsapi.py          ← NewsAPI.org adapter
```
