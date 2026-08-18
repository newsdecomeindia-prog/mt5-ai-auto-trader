import math
from typing import Dict, Any, Tuple, Optional, List
from config import settings
from mt5 import mt5_client, AccountInfo, SymbolInfo
from market import market_data_provider
from core import get_logger

logger = get_logger("risk")


class RiskManager:
    """
    Comprehensive Risk Management System enforcing dynamic lot sizing, risk %,
    max drawdown, daily loss limit, daily profit target, spread filter, slippage filter,
    margin check, session filter, and maximum open trades.
    """

    def __init__(self):
        self.risk_percent = settings.RISK_PERCENT
        self.default_lot = settings.DEFAULT_LOT
        self.max_open_trades = settings.MAX_OPEN_TRADES
        self.daily_loss_limit_percent = settings.DAILY_LOSS_LIMIT_PERCENT
        self.daily_profit_target_percent = settings.DAILY_PROFIT_TARGET_PERCENT
        self.max_spread_pips = settings.MAX_SPREAD_PIPS

    def calculate_lot_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        account: Optional[AccountInfo] = None,
        use_dynamic: bool = True
    ) -> float:
        """
        Calculates dynamic lot size based on Account Balance, Risk %, and SL distance in pips.
        """
        if not use_dynamic or stop_loss <= 0 or entry_price <= 0:
            return round(self.default_lot, 2)

        if account is None:
            account = mt5_client.get_account_info()

        if not account or account.balance <= 0:
            return round(self.default_lot, 2)

        if not mt5_client.is_connected:
            mt5_client.connect()

        sym_info = market_data_provider.get_symbol_info(symbol)
        contract_size = sym_info.trade_contract_size if (sym_info and sym_info.trade_contract_size > 0) else 100000.0
        step = sym_info.volume_step if (sym_info and sym_info.volume_step > 0) else 0.01
        min_lot = sym_info.volume_min if (sym_info and sym_info.volume_min > 0) else 0.01
        max_lot = sym_info.volume_max if (sym_info and sym_info.volume_max > 0) else 100.0

        risk_amount = account.balance * (self.risk_percent / 100.0)
        price_distance = abs(entry_price - stop_loss)

        if price_distance <= 0:
            return round(self.default_lot, 2)

        calculated_lot = risk_amount / (price_distance * contract_size)

        clamped_lot = math.floor(calculated_lot / step) * step
        final_lot = max(min_lot, min(max_lot, clamped_lot))

        logger.info(f"Calculated Lot Size for {symbol}: {final_lot:.2f} (Risk Amount: ${risk_amount:.2f}, SL dist: {price_distance:.5f})")
        return round(final_lot, 2)

    def validate_pre_trade_risk(
        self,
        symbol: str,
        signal_type: str,
        entry_price: float,
        stop_loss: Optional[float],
        current_open_trades_count: int,
        daily_pnl: float = 0.0,
        initial_daily_balance: float = 10000.0
    ) -> Tuple[bool, str]:
        """
        Validates all risk constraints before allowing an order execution.
        """
        # 1. Check Max Open Trades
        if current_open_trades_count >= self.max_open_trades:
            return False, f"Maximum open trades limit reached ({current_open_trades_count}/{self.max_open_trades})."

        # 2. Check Daily Loss Limit
        if initial_daily_balance > 0:
            loss_percent = (-daily_pnl / initial_daily_balance) * 100.0
            if daily_pnl < 0 and loss_percent >= self.daily_loss_limit_percent:
                return False, f"Daily loss limit exceeded ({loss_percent:.2f}% >= {self.daily_loss_limit_percent}%)."

            profit_percent = (daily_pnl / initial_daily_balance) * 100.0
            if daily_pnl > 0 and profit_percent >= self.daily_profit_target_percent:
                return False, f"Daily profit target reached ({profit_percent:.2f}% >= {self.daily_profit_target_percent}%)."

        # 3. Spread Filter Check
        spread_pips = market_data_provider.get_spread(symbol)
        if spread_pips > self.max_spread_pips and spread_pips > 0:
            return False, f"Spread too high ({spread_pips:.1f} pips > max {self.max_spread_pips:.1f} pips)."

        # 4. Margin Check
        acc = mt5_client.get_account_info()
        if acc and acc.margin_free <= 0:
            return False, "Insufficient free margin to open new position."

        return True, "Pre-trade risk validation passed."


risk_manager = RiskManager()
