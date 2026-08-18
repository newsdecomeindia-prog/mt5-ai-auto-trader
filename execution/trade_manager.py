from typing import List, Dict, Any, Tuple
from database import db_manager, TradeRepository, TradeStatus
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
        with db_manager.get_session() as session:
            trade_repo = TradeRepository(session)
            open_trades = trade_repo.get_open_trades()

            for trade in open_trades:
                tick = mt5_client.get_tick(trade.symbol)
                if not tick:
                    continue

                curr_price = tick.bid if trade.order_type == "BUY" else tick.ask
                pips = (curr_price - trade.open_price) * 10000.0 if trade.order_type == "BUY" else (trade.open_price - curr_price) * 10000.0

                action_taken = None

                # 1. Break Even Check
                if pips >= self.break_even_pips and (trade.stop_loss is None or (trade.order_type == "BUY" and trade.stop_loss < trade.open_price) or (trade.order_type == "SELL" and trade.stop_loss > trade.open_price)):
                    new_sl = trade.open_price + 0.0001 if trade.order_type == "BUY" else trade.open_price - 0.0001
                    execution_engine.modify_order(trade.ticket, stop_loss=new_sl, take_profit=trade.take_profit)
                    action_taken = "BREAK_EVEN_MOVED"
                    logger.info(f"Trade {trade.ticket} moved to Break-Even at {new_sl:.5f}")

                # 2. Trailing Stop Check
                if pips >= self.trailing_stop_pips:
                    dist = (self.trailing_stop_pips / 10000.0)
                    new_sl = curr_price - dist if trade.order_type == "BUY" else curr_price + dist
                    if trade.order_type == "BUY" and (trade.stop_loss is None or new_sl > trade.stop_loss):
                        execution_engine.modify_order(trade.ticket, stop_loss=new_sl, take_profit=trade.take_profit)
                        action_taken = "TRAILING_STOP_UPDATED"
                    elif trade.order_type == "SELL" and (trade.stop_loss is None or new_sl < trade.stop_loss):
                        execution_engine.modify_order(trade.ticket, stop_loss=new_sl, take_profit=trade.take_profit)
                        action_taken = "TRAILING_STOP_UPDATED"

                # 3. Hit Stop Loss or Take Profit check
                if trade.stop_loss and ((trade.order_type == "BUY" and curr_price <= trade.stop_loss) or (trade.order_type == "SELL" and curr_price >= trade.stop_loss)):
                    execution_engine.close_trade(trade.ticket, exit_reason="STOP_LOSS_HIT")
                    action_taken = "STOP_LOSS_HIT"

                elif trade.take_profit and ((trade.order_type == "BUY" and curr_price >= trade.take_profit) or (trade.order_type == "SELL" and curr_price <= trade.take_profit)):
                    execution_engine.close_trade(trade.ticket, exit_reason="TAKE_PROFIT_HIT")
                    action_taken = "TAKE_PROFIT_HIT"

                if action_taken:
                    results.append({
                        "ticket": trade.ticket,
                        "symbol": trade.symbol,
                        "action": action_taken,
                        "current_price": curr_price
                    })

        return results

    def emergency_close_all(self, reason: str = "EMERGENCY_CLOSE") -> List[Tuple[int, bool]]:
        """
        Immediately closes all open trades in the platform.
        """
        outcomes = []
        with db_manager.get_session() as session:
            trade_repo = TradeRepository(session)
            open_trades = trade_repo.get_open_trades()

            for trade in open_trades:
                ok, msg = execution_engine.close_trade(trade.ticket, exit_reason=reason)
                outcomes.append((trade.ticket, ok))

        logger.warning(f"Emergency Close All triggered. Total closed: {len(outcomes)}. Reason: {reason}")
        return outcomes


trade_manager = TradeManager()
