import pytest
from execution import execution_engine, trade_manager
from database import DatabaseManager, db_manager, TradeRepository, TradeStatus


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    db_file = tmp_path / "test_mt5.db"
    test_db = DatabaseManager(f"sqlite:///{db_file}")
    test_db.init_db()

    monkeypatch.setattr("database.connection.db_manager", test_db)
    monkeypatch.setattr("database.db_manager", test_db)
    monkeypatch.setattr("execution.engine.db_manager", test_db)
    return test_db


def test_order_execution_and_close(setup_test_db):
    ok, ticket, msg = execution_engine.execute_order(
        symbol="EURUSD",
        order_type="BUY",
        volume=0.1,
        price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        comment="Test Order"
    )
    assert ok is True
    assert ticket is not None

    # Verify order in DB
    with setup_test_db.get_session() as session:
        trade_repo = TradeRepository(session)
        trade = trade_repo.get_by_ticket(ticket)
        assert trade is not None
        assert trade.symbol == "EURUSD"
        assert trade.status == TradeStatus.OPEN.value

    # Close trade
    close_ok, close_msg = execution_engine.close_trade(ticket, exit_reason="TEST_CLOSE")
    assert close_ok is True

    with setup_test_db.get_session() as session:
        trade_repo = TradeRepository(session)
        trade = trade_repo.get_by_ticket(ticket)
        assert trade.status == TradeStatus.CLOSED.value


def test_emergency_close_all(setup_test_db):
    execution_engine.execute_order("EURUSD", "BUY", 0.1, price=1.0850)
    execution_engine.execute_order("GBPUSD", "BUY", 0.1, price=1.2700)

    results = trade_manager.emergency_close_all(reason="TEST_EMERGENCY")
    assert len(results) == 2
    assert all(r[1] for r in results)
