import pytest
from risk import risk_manager
from portfolio import portfolio_manager
from mt5 import AccountInfo
from database import Trade, TradeStatus


def test_dynamic_lot_calculation():
    acc = AccountInfo(login=12345, balance=10000.0, equity=10000.0, margin_free=10000.0)

    # 1.0850 entry, 1.0800 SL -> 0.0050 distance (50 pips)
    # Risk 1% of 10,000 = $100 -> Lot = 100 / (0.0050 * 100,000) = 0.20 lots
    lot = risk_manager.calculate_lot_size("EURUSD", 1.0850, 1.0800, account=acc, use_dynamic=True)
    assert lot == 0.20


def test_risk_manager_pre_trade_validation():
    # 1. Valid case
    valid, msg = risk_manager.validate_pre_trade_risk("EURUSD", "BUY", 1.0850, 1.0800, current_open_trades_count=1)
    assert valid is True

    # 2. Max open trades exceeded
    valid_max, msg_max = risk_manager.validate_pre_trade_risk("EURUSD", "BUY", 1.0850, 1.0800, current_open_trades_count=10)
    assert valid_max is False
    assert "Maximum open trades limit reached" in msg_max

    # 3. Daily loss limit hit
    valid_loss, msg_loss = risk_manager.validate_pre_trade_risk("EURUSD", "BUY", 1.0850, 1.0800, current_open_trades_count=1, daily_pnl=-600.0, initial_daily_balance=10000.0)
    assert valid_loss is False
    assert "Daily loss limit exceeded" in msg_loss


def test_portfolio_exposure_management():
    trades = [
        Trade(ticket=1, symbol="EURUSD", volume=0.5, status=TradeStatus.OPEN.value),
        Trade(ticket=2, symbol="GBPUSD", volume=0.5, status=TradeStatus.OPEN.value),
        Trade(ticket=3, symbol="USDJPY", volume=0.5, status=TradeStatus.OPEN.value),
    ]

    # Valid portfolio check
    valid, msg = portfolio_manager.check_portfolio_exposure("AUDUSD", 0.1, open_trades=trades, total_daily_trades_count=3)
    assert valid is True

    # Exceed symbol exposure (EURUSD max 2.0 lots)
    valid_sym, msg_sym = portfolio_manager.check_portfolio_exposure("EURUSD", 2.0, open_trades=trades, total_daily_trades_count=3)
    assert valid_sym is False
    assert "Maximum exposure for symbol" in msg_sym
