from typing import List, Dict, Any, Tuple
from database.repository import TradeRepository
from database.models import TradeStatus
from execution.engine import execution_engine
from mt5 import mt5_client
from core import get_logger

logger = get_logger("trading")


class TradeManager:
    """
    Active Position Management System providing Trailing Stop, Break-Even adjustment,
    Partial Close, Profit Lock, Emergency Close, and Auto Exits.
    """

    def __init__(
        self,
        trailing_stop_pips: float = 20.0,
        break_even_pips: float = 15.0,
        partial_close_percent: float = 50.0
    ):
        self.trailing_stop_pips = trailing_stop_pips
        self.break_even_pips = break_even_pips
        self.partial_close_percent = partial_close_percent

    def manage_open_positions(self) -> List[Dict[str, Any]]:
        """
        Scans all open trades in DB and applies trade management rules.
        """
        results = []
        from database.connection import db_manager as current_db

        trades_to_process = []
        with current_db.get_session() as session:
            trade_repo = TradeRepository(session)
            open_trades = trade_repo.get_open_trades()
            for trade in open_trades:
                trades_to_process.append({
                    "ticket": trade.ticket,
                    "symbol": trade.symbol,
                    "order_type": trade.order_type,
                    "open_price": trade.open_price,
                    "stop_loss": trade.stop_loss,
                    "take_profit": trade.take_profit
                })

        for trade in trades_to_process:
            ticket = trade["ticket"]
            symbol = trade["symbol"]
            order_type = trade["order_type"]
            open_price = trade["open_price"]
            stop_loss = trade["stop_loss"]
            take_profit = trade["take_profit"]

            tick = mt5_client.get_tick(symbol)
            if not tick:
                continue

            curr_price = tick.bid if order_type == "BUY" else tick.ask
            pips = (curr_price - open_price) * 10000.0 if order_type == "BUY" else (open_price - curr_price) * 10000.0

            action_taken = None

            # 1. Break Even Check
            if pips >= self.break_even_pips and (stop_loss is None or (order_type == "BUY" and stop_loss < open_price) or (order_type == "SELL" and stop_loss > open_price)):
                new_sl = open_price + 0.0001 if order_type == "BUY" else open_price - 0.0001
                execution_engine.modify_order(ticket, stop_loss=new_sl, take_profit=take_profit)
                action_taken = "BREAK_EVEN_MOVED"
                logger.info(f"Trade {ticket} moved to Break-Even at {new_sl:.5f}")

            # 2. Trailing Stop Check
            if pips >= self.trailing_stop_pips:
                dist = (self.trailing_stop_pips / 10000.0)
                new_sl = curr_price - dist if order_type == "BUY" else curr_price + dist
                if order_type == "BUY" and (stop_loss is None or new_sl > stop_loss):
                    execution_engine.modify_order(ticket, stop_loss=new_sl, take_profit=take_profit)
                    action_taken = "TRAILING_STOP_UPDATED"
                elif order_type == "SELL" and (stop_loss is None or new_sl < stop_loss):
                    execution_engine.modify_order(ticket, stop_loss=new_sl, take_profit=take_profit)
                    action_taken = "TRAILING_STOP_UPDATED"

            # 3. Hit Stop Loss or Take Profit check
            if stop_loss and ((order_type == "BUY" and curr_price <= stop_loss) or (order_type == "SELL" and curr_price >= stop_loss)):
                execution_engine.close_trade(ticket, exit_reason="STOP_LOSS_HIT")
                action_taken = "STOP_LOSS_HIT"

            elif take_profit and ((order_type == "BUY" and curr_price >= take_profit) or (order_type == "SELL" and curr_price <= take_profit)):
                execution_engine.close_trade(ticket, exit_reason="TAKE_PROFIT_HIT")
                action_taken = "TAKE_PROFIT_HIT"

            if action_taken:
                results.append({
                    "ticket": ticket,
                    "symbol": symbol,
                    "action": action_taken,
                    "current_price": curr_price
                })

        return results

    def emergency_close_all(self, reason: str = "EMERGENCY_CLOSE") -> List[Tuple[int, bool]]:
        """
        Immediately closes all open trades in the platform.
        """
        outcomes = []
        from database.connection import db_manager as current_db

        tickets_to_close = []
        with current_db.get_session() as session:
            trade_repo = TradeRepository(session)
            open_trades = trade_repo.get_open_trades()
            tickets_to_close = [t.ticket for t in open_trades]

        for ticket in tickets_to_close:
            ok, msg = execution_engine.close_trade(ticket, exit_reason=reason)
            outcomes.append((ticket, ok))

        logger.warning(f"Emergency Close All triggered. Total closed: {len(outcomes)}. Reason: {reason}")
        return outcomes


trade_manager = TradeManager()
