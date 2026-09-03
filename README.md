# MT5 AI Auto Trading Platform

Production-grade MetaTrader 5 AI Auto Trading Platform built with Python 3.12+, FastAPI, SQLAlchemy, Loguru, Pydantic v2, Smart Money Concepts (SMC), ICT Concepts, Technical Indicators, Risk Management, Telegram Bot, Plotly Web Dashboard, and Docker.

---

## Key Features

- **MT5 Engine**: Auto Login, Auto Reconnect, Connection Health Monitor, Market Watch Sync, and Paper Simulation Fallback.
- **Multi-Market Scanner**: Forex, Gold, Silver, Crypto, Indices, CFDs across timeframes (M1 to MN1).
- **Technical Indicators**: EMA, SMA, RSI, MACD, ADX, ATR, VWAP, CCI, Momentum, Stochastic, SuperTrend, Bollinger Bands, Ichimoku, Donchian Channel.
- **Price Action & SMC**: Pin Bar, Engulfing, Inside/Outside Bar, Order Blocks, Breaker Blocks, Fair Value Gaps (FVG), Liquidity Sweeps, BOS, CHOCH, Premium/Discount zones.
- **ICT Concepts**: Optimal Trade Entry (OTE), Kill Zones, Power Of Three (AMD), Judas Swing, Liquidity Pools, Daily Bias.
- **AI Signal Engine**: Multi-factor signal generation with Confidence, Trade, and Probability Scores.
- **Smart Risk & Portfolio Management**: Dynamic Lot Sizing, Fixed Lot, Risk %, Drawdown Limits, Daily Loss/Profit Targets, Spread Filter, Margin Check, Currency & Symbol Exposure.
- **Execution & Trade Management**: Market & Pending Orders, Trailing Stop, Break-Even Adjustment, Partial Close, Emergency Close.
- **Analytics & Backtesting**: Historical Backtester, Walk-Forward Testing, Win Rate, Profit Factor, Expectancy, Equity Curve.
- **Telegram Bot**: Async trade open/close alerts, SL/TP notifications, error alerts, daily/weekly summaries.
- **FastAPI REST & WebSockets**: Full REST API, real-time `/ws/live` streaming, rate-limiting, and input validation.
- **Mobile Responsive Web Dashboard**: Plotly charts, live balance/equity/margin cards, open positions table, and system controls.
- **Deployment & CI/CD**: Multi-stage Dockerfile, Docker Compose, SQLite backup/restore, and GitHub Actions CI workflow.

---

## Quick Start Guide

### 1. Install & Run locally:
```bash
git clone <repo_url>
cd mt5-ai-auto-trader
pip install -r requirements.txt
cp .env.example .env
python run.py
```

### 2. Run with Docker Compose:
```bash
docker-compose up -d --build
```

Access the dashboard at `http://localhost:8000`.

---

## Running Tests

```bash
pytest --verbose
```
