import pytest
from mt5 import mt5_client, health_monitor, AccountInfo, SymbolInfo, TickData


def test_mt5_connection():
    connected = mt5_client.connect()
    assert connected is True
    assert mt5_client.is_connected is True


def test_mt5_account_info():
    mt5_client.connect()
    acc = mt5_client.get_account_info()
    assert acc is not None
    assert isinstance(acc, AccountInfo)
    assert acc.balance >= 0


def test_mt5_symbol_and_tick():
    mt5_client.connect()
    mt5_client.sync_market_watch(["EURUSD", "XAUUSD"])
    sym = mt5_client.get_symbol_info("EURUSD")
    assert sym is not None
    assert isinstance(sym, SymbolInfo)
    assert sym.name == "EURUSD"

    tick = mt5_client.get_tick("EURUSD")
    assert tick is not None
    assert isinstance(tick, TickData)
    assert tick.ask > 0
    assert tick.bid > 0


def test_mt5_health_check():
    mt5_client.connect()
    health = health_monitor.check_health()
    assert health["status"] == "healthy"
    assert health["latency_ms"] >= 0
