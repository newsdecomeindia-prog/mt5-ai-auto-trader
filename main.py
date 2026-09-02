import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from core import get_logger
from database import db_manager, TradeRepository, PerformanceRepository
from mt5 import mt5_client, health_monitor
from scanner import market_scanner, MarketCategory
from market import market_data_provider
from strategy import composite_ai_strategy
from risk import risk_manager
from portfolio import portfolio_manager
from execution import execution_engine, trade_manager
from telegram import telegram_notifier
from api import api_router, SYSTEM_STATE
from dashboard import dashboard_router

logger = get_logger("general")

# APScheduler instance
scheduler = AsyncIOScheduler()


async def scheduled_trading_cycle():
    """Main automated trading engine loop."""
    if not SYSTEM_STATE["is_running"]:
        return

    try:
        # 1. MT5 Health Check & Connection Maintenance
        health = health_monitor.check_health()
        if health["status"] != "healthy":
            logger.warning("MT5 engine is unhealthy. Skipping trading cycle.")
            return

        # 2. Manage Active Open Positions (Trailing SL, Break-Even, TP/SL hits)
        trade_manager.manage_open_positions()

        # 3. Market Watch Scanning
        active_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"]
        mt5_client.sync_market_watch(active_symbols)

        # Retrieve open trades within session
        with db_manager.get_session() as session:
            trade_repo = TradeRepository(session)
            open_trades = list(trade_repo.get_open_trades())
            current_open_count = len(open_trades)

        for sym in active_symbols:
            df = market_data_provider.get_ohlc(sym, timeframe="H1", count=100)
            df_daily = market_data_provider.get_ohlc(sym, timeframe="D1", count=50)

            if df.empty:
                continue

            # 4. Generate Signal
            sig = composite_ai_strategy.analyze(sym, df, df_daily=df_daily)

            if sig.signal_type in ("BUY", "SELL") and sig.scores.confidence_score >= 60.0:
                logger.info(f"Generated {sig.signal_type} Signal for {sym} (Confidence: {sig.scores.confidence_score}%)")

                # 5. Risk & Portfolio Validation
                risk_ok, risk_msg = risk_manager.validate_pre_trade_risk(
                    symbol=sym,
                    signal_type=sig.signal_type,
                    entry_price=sig.entry_price,
                    stop_loss=sig.stop_loss,
                    current_open_trades_count=current_open_count
                )

                if not risk_ok:
                    logger.warning(f"Trade blocked by Risk Manager: {risk_msg}")
                    continue

                lot_size = risk_manager.calculate_lot_size(sym, sig.entry_price, sig.stop_loss or (sig.entry_price - 0.0050))

                port_ok, port_msg = portfolio_manager.check_portfolio_exposure(sym, lot_size, open_trades=open_trades)
                if not port_ok:
                    logger.warning(f"Trade blocked by Portfolio Manager: {port_msg}")
                    continue

                # 6. Execute Order
                exec_ok, ticket, exec_msg = execution_engine.execute_order(
                    symbol=sym,
                    order_type=sig.signal_type,
                    volume=lot_size,
                    price=sig.entry_price,
                    stop_loss=sig.stop_loss,
                    take_profit=sig.take_profit
                )

                if exec_ok and ticket:
                    telegram_notifier.notify_trade_open(
                        symbol=sym,
                        order_type=sig.signal_type,
                        volume=lot_size,
                        price=sig.entry_price,
                        sl=sig.stop_loss,
                        tp=sig.take_profit,
                        ticket=ticket
                    )

    except Exception as e:
        logger.error(f"Error in trading cycle loop: {e}")
        telegram_notifier.notify_error("EngineLoop", str(e))


async def scheduled_performance_snapshot():
    """Records periodic performance snapshot in database."""
    try:
        acc = mt5_client.get_account_info()
        if acc:
            with db_manager.get_session() as session:
                perf_repo = PerformanceRepository(session)
                perf_repo.record_snapshot(
                    balance=acc.balance,
                    equity=acc.equity,
                    margin=acc.margin,
                    free_margin=acc.margin_free,
                    open_pnl=acc.profit
                )
    except Exception as e:
        logger.error(f"Error taking performance snapshot: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler initializing DB, MT5 connection, and scheduler."""
    logger.info("Initializing MT5 AI Auto Trading Platform...")

    # Initialize Database
    db_manager.init_db()

    # Connect MT5 Client
    mt5_client.connect()

    # Schedule trading cycles every 10 seconds
    scheduler.add_job(scheduled_trading_cycle, 'interval', seconds=10, id='trading_cycle')
    scheduler.add_job(scheduled_performance_snapshot, 'interval', minutes=5, id='perf_snapshot')
    scheduler.start()
    logger.info("Trading cycle scheduler started.")

    yield

    # Shutdown logic
    logger.info("Shutting down MT5 AI Auto Trading Platform...")
    scheduler.shutdown()
    mt5_client.disconnect()


app = FastAPI(
    title="MT5 AI Auto Trading Platform",
    version="1.0.0",
    description="Production MetaTrader 5 AI Auto Trading Engine with SMC, ICT, Risk Management, FastAPI, Telegram and Web Dashboard.",
    lifespan=lifespan
)

# Include routers
app.include_router(dashboard_router, prefix="", tags=["Dashboard"])
app.include_router(api_router, prefix="/api/v1", tags=["API"])


@app.get("/health")
async def health():
    return health_monitor.check_health()
