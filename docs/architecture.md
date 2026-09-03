# Architecture Documentation

## MT5 AI Auto Trading Platform Architecture

The MT5 AI Auto Trading Platform is designed using a clean, modular, domain-driven architecture following SOLID principles.

### System Modules

1. **Config (`config/`)**: Centralized Pydantic Settings v2 management.
2. **Core (`core/`)**: Loguru structured logging and security/rate-limiting utilities.
3. **MT5 Engine (`mt5/`)**: MetaTrader 5 API client wrapper with auto-login, auto-reconnect, health monitoring, market watch synchronization, and fallback paper trading simulation driver.
4. **Market Data & Scanner (`market/`, `scanner/`)**: Live ticks, historical bar fetching, spread calculation, ATR, volume, market depth, and multi-asset watch scanner (Forex, Gold, Silver, Crypto, Indices, CFDs).
5. **Technical Indicators (`indicators/`)**: Pure NumPy/Pandas technical analysis engine (EMA, SMA, RSI, MACD, ADX, ATR, VWAP, CCI, Momentum, Stochastic, SuperTrend, Bollinger Bands, Ichimoku, Donchian Channel).
6. **Price Action (`strategy/price_action.py`)**: Candlestick & chart pattern recognition (Pin Bar, Hammer, Shooting Star, Engulfing, Inside/Outside Bar, Breakout, Retest, Trend Continuation).
7. **Smart Money Concepts (`smc/`)**: Institutional pattern detector (Order Blocks, Breaker/Mitigation Blocks, FVG, Liquidity Sweeps, EQH/EQL, BOS, CHOCH, Premium/Discount zones).
8. **ICT Concepts (`ict/`)**: Inner Circle Trader engine (Optimal Trade Entry, Kill Zones, Power Of Three / AMD, Judas Swing, Liquidity Pools, Daily Bias).
9. **Signal Engine & Strategy (`signals/`, `strategy/`)**: Multi-factor AI signal engine generating scored BUY/SELL/NO_TRADE signals with confidence and probability scoring.
10. **Risk & Portfolio Management (`risk/`, `portfolio/`)**: Dynamic lot size calculator, risk % control, daily drawdown limits, daily profit target, spread filter, margin check, and exposure controls.
11. **Execution & Trade Management (`execution/`)**: Order placement, SL/TP modification, order cancellation, trailing stop, break-even adjustment, partial close, and emergency close.
12. **Database (`database/`)**: SQLite storage with SQLAlchemy models and repositories for Trades, Orders, Signals, Logs, Settings, Statistics, and PerformanceRecords.
13. **Analytics & Backtesting (`analytics/`)**: Historical backtester, walk-forward testing, and performance metrics (win rate, profit factor, expectancy, drawdown).
14. **Telegram (`telegram/`)**: Async Telegram bot notifications for trade alerts and performance summaries.
15. **API & Dashboard (`api/`, `dashboard/`)**: FastAPI REST endpoints, WebSocket live updates (`/ws/live`), and mobile-responsive Plotly web dashboard.
