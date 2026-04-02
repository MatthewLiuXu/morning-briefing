# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A crypto hedge fund morning briefing generator. Fetches market data, social metrics, and news, then synthesizes them into a daily brief via Claude AI and posts to Slack.

## Running

```bash
python main.py
```

No build step, no test suite. All configuration via `.env` and `config.py`.

## Dependencies

No `requirements.txt` exists. Inferred dependencies:
- `anthropic` — Claude SDK
- `requests` — HTTP client
- `python-dotenv` — `.env` loading

Install with: `pip install anthropic requests python-dotenv`

## Environment Setup

Copy `.env` and populate:
- `ANTHROPIC_API_KEY`
- `CRYPTOPANIC_API_KEY`
- `LUNARCRUSH_API_KEY`
- `SLACK_WEBHOOK_URL`

## Architecture

4-stage pipeline in `main.py:run()`:

1. **Gather** — parallel data fetches from `data_sources/` (CoinGecko, Binance, CryptoPanic, LunarCrush, portfolio config)
2. **Enrich** — `enrichment.py:enrich_data()` calculates portfolio PnL, flags alerts (>5% price move, >0.05% funding rate, >100% social spike), structures into a single dict
3. **Synthesize** — `synthesizer.py:synthesize_briefing()` sends enriched JSON to `claude-sonnet-4-20250514` with a system prompt that enforces a 7-section format (TOP LINE, PORTFOLIO, MARKET, FUNDING, SOCIAL, NEWS, NEEDS ATTENTION), max 400 words
4. **Deliver** — `delivery.py:post_to_slack()` posts via webhook

Each data source failure is caught individually and reported in `data_source_errors` — the pipeline continues on partial failures.

## Key Configuration (`config.py`)

- `PORTFOLIO_TOKENS` — token IDs (CoinGecko format), quantity, and entry price
- `FUNDING_SYMBOLS` — Binance perp symbols to track
- Alert thresholds: `PRICE_ALERT_THRESHOLD = 0.05`, `FUNDING_ALERT_THRESHOLD = 0.0005`

## Extending

- **Add a data source**: create a module in `data_sources/`, add call in `main.py:run()`, merge result into `raw_data`, handle in `enrichment.py`
- **Change delivery**: `delivery.py` has a commented SendGrid email template; the pattern is the same for Discord/Telegram
- **Portfolio integration**: `data_sources/portfolio.py` has a commented Google Sheets template — replace `get_portfolio()` to pull live positions
