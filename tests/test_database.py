import pytest
from database import (
    DatabaseManager, TradeRepository, OrderRepository, SignalRepository,
    LogRepository, SettingRepository, StatisticsRepository, PerformanceRepository,
    TradeStatus, OrderStatus
)


@pytest.fixture
def db_mgr():
    mgr = DatabaseManager("sqlite:///:memory:")
    mgr.init_db()
    return mgr


def test_database_init(db_mgr):
    with db_mgr.get_session() as session:
        assert session is not None


def test_trade_repository(db_mgr):
    with db_mgr.get_session() as session:
        repo = TradeRepository(session)
        trade = repo.create(
            ticket=1001,
            symbol="EURUSD",
            order_type="BUY",
            volume=0.1,
            open_price=1.0850,
            stop_loss=1.0800,
            take_profit=1.0950,
            status=TradeStatus.OPEN.value
        )
        assert trade.id is not None
        assert trade.ticket == 1001

        open_trades = repo.get_open_trades("EURUSD")
        assert len(open_trades) == 1

        closed = repo.close_trade(ticket=1001, close_price=1.0900, profit=50.0, exit_reason="TP Hit")
        assert closed.status == TradeStatus.CLOSED.value
        assert closed.profit == 50.0

        open_trades_after = repo.get_open_trades("EURUSD")
        assert len(open_trades_after) == 0


def test_order_repository(db_mgr):
    with db_mgr.get_session() as session:
        repo = OrderRepository(session)
        order = repo.create(
            order_id=2001,
            symbol="XAUUSD",
            order_type="BUY_LIMIT",
            price=2000.0,
            volume=0.2,
            status=OrderStatus.PENDING.value
        )
        assert order.order_id == 2001

        pending = repo.get_pending_orders("XAUUSD")
        assert len(pending) == 1

        updated = repo.update_status(2001, OrderStatus.FILLED.value)
        assert updated.status == OrderStatus.FILLED.value


def test_signal_repository(db_mgr):
    with db_mgr.get_session() as session:
        repo = SignalRepository(session)
        sig = repo.create(
            symbol="BTCUSD",
            timeframe="H1",
            signal_type="BUY",
            confidence_score=85.5,
            trade_score=90.0,
            probability_score=80.0
        )
        assert sig.id is not None

        latest = repo.get_latest("BTCUSD")
        assert len(latest) == 1
        assert latest[0].signal_type == "BUY"


def test_log_setting_stats_performance_repos(db_mgr):
    with db_mgr.get_session() as session:
        log_repo = LogRepository(session)
        setting_repo = SettingRepository(session)
        stats_repo = StatisticsRepository(session)
        perf_repo = PerformanceRepository(session)

        # Log
        log_entry = log_repo.log("Trading", "Order placed successfully")
        assert log_entry.id is not None

        # Setting
        setting_repo.set("RISK_LEVEL", "MEDIUM", "Current risk setting")
        val = setting_repo.get("RISK_LEVEL")
        assert val == "MEDIUM"

        # Statistics
        stats_repo.save_stats(
            total_trades=10,
            winning_trades=7,
            losing_trades=3,
            win_rate=70.0,
            total_profit=350.0
        )
        latest_stat = stats_repo.get_latest()
        assert latest_stat.win_rate == 70.0

        # Performance
        perf_repo.record_snapshot(balance=10000.0, equity=10200.0, open_pnl=200.0)
        history = perf_repo.get_history()
        assert len(history) == 1
        assert history[0].equity == 10200.0
