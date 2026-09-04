# Trade Setup Telegram Bot

A research-oriented Telegram bot for daily crypto and stock trade setups. It combines technical indicators with crypto whale-flow signals and produces risk-defined LONG/SHORT/WAIT setups.

## Architecture
- FastAPI-compatible Python service
- Telegram bot interface
- Scheduled daily scan
- Crypto market data adapter
- Stock market data adapter
- Whale-flow adapter for blockchain transfers and exchange flows
- Technical scoring engine
- Risk/reward engine
- SQLite/Postgres-ready trade journal

## Signals
Crypto: price structure, EMA 20/50/200, RSI, MACD, ATR, volume, support/resistance, whale accumulation/distribution and exchange-flow context.

Stocks: price structure, indicators, volume and configurable watchlist. Institutional/flow adapters can be added where a licensed data source provides the relevant data.

Whale activity is confirmation, not a standalone prediction. Transfers are classified by source/destination context and confidence.

## Telegram commands
/start /today /crypto /stocks /setup <symbol> /watchlist /performance /help

## Environment
Copy `.env.example` to `.env` and configure secrets. Never commit API keys or Telegram bot tokens.

## Disclaimer
Signals are informational market analysis, not guaranteed returns or personalized financial advice. Users should independently verify data and manage risk.
