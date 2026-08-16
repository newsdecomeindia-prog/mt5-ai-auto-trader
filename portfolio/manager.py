from typing import List, Dict, Any, Tuple
from database import Trade, TradeStatus
from core import get_logger

logger = get_logger("risk")


class PortfolioManager:
    """
    Portfolio Management System controlling symbol exposure, currency exposure,
    and daily total trade limits.
    """

    def __init__(self, max_symbol_exposure_lots: float = 2.0, max_daily_trades: int = 20):
        self.max_symbol_exposure_lots = max_symbol_exposure_lots
        self.max_daily_trades = max_daily_trades

    def check_portfolio_exposure(
        self,
        symbol: str,
        requested_lot: float,
        open_trades: List[Trade],
        total_daily_trades_count: int = 0
    ) -> Tuple[bool, str]:
        """
        Validates exposure across portfolio.
        """
        # 1. Daily Total Trades Limit Check
        if total_daily_trades_count >= self.max_daily_trades:
            return False, f"Maximum daily total trades limit reached ({total_daily_trades_count}/{self.max_daily_trades})."

        # 2. Current Symbol Volume Exposure
        current_symbol_lots = sum(t.volume for t in open_trades if t.symbol == symbol and t.status == TradeStatus.OPEN.value)
        if current_symbol_lots + requested_lot > self.max_symbol_exposure_lots:
            return False, f"Maximum exposure for symbol {symbol} exceeded ({current_symbol_lots + requested_lot:.2f} > max {self.max_symbol_exposure_lots:.2f} lots)."

        # 3. Currency Over-exposure Check (e.g. max 3 USD-based trades)
        base_currency = symbol[:3]
        quote_currency = symbol[3:] if len(symbol) >= 6 else ""

        usd_trades = 0
        for t in open_trades:
            if t.status == TradeStatus.OPEN.value and ("USD" in t.symbol):
                usd_trades += 1

        if "USD" in symbol and usd_trades >= 4:
            return False, f"Maximum currency exposure limit reached for USD trades ({usd_trades} open)."

        return True, "Portfolio exposure check passed."


portfolio_manager = PortfolioManager()
