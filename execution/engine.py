import time
from typing import Dict, Any, Optional, Tuple, List
from config import settings
from mt5 import mt5_client, TickData
from database.repository import TradeRepository, OrderRepository
from database.models import TradeStatus, OrderStatus, OrderType
from core import get_logger

logger = get_logger("trading")


class ExecutionEngine:
    """
    Handles order execution (Market Buy/Sell, Limit, Stop orders), modification,
    cancellation, retry logic for failed orders, and database synchronization.
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 0.5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def execute_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        comment: str = "MT5 AI Trader",
        magic: int = settings.MAGIC_NUMBER
    ) -> Tuple[bool, Optional[int], str]:
        """
        Executes order with auto retry on failure.
        Order Types: BUY, SELL, BUY_LIMIT, SELL_LIMIT, BUY_STOP, SELL_STOP.
        """
        if not mt5_client.is_connected:
            mt5_client.connect()

        tick = mt5_client.get_tick(symbol)
        if not tick and price is None:
            return False, None, f"Failed to retrieve tick for {symbol}"

        curr_price = price if price is not None else (tick.ask if "BUY" in order_type else tick.bid)

        for attempt in range(1, self.max_retries + 1):
            try:
                ticket = None
                if mt5_client.is_simulated:
                    ticket = int(time.time() * 1000) % 10000000
                    logger.info(f"[SIMULATED EXECUTION] {order_type} {volume} {symbol} @ {curr_price:.5f} (SL: {stop_loss}, TP: {take_profit}) -> Ticket: {ticket}")

                    from database.connection import db_manager as current_db
                    with current_db.get_session() as session:
                        trade_repo = TradeRepository(session)
                        trade_repo.create(
                            ticket=ticket,
                            symbol=symbol,
                            order_type=order_type,
                            volume=volume,
                            open_price=curr_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            status=TradeStatus.OPEN.value,
                            magic_number=magic,
                            comment=comment
                        )

                    return True, ticket, "Order executed successfully (Simulated)"

                else:
                    mt5 = mt5_client.driver
                    action = mt5.TRADE_ACTION_DEAL if order_type in ("BUY", "SELL") else mt5.TRADE_ACTION_PENDING
                    type_dict = {
                        "BUY": mt5.ORDER_TYPE_BUY,
                        "SELL": mt5.ORDER_TYPE_SELL,
                        "BUY_LIMIT": mt5.ORDER_TYPE_BUY_LIMIT,
                        "SELL_LIMIT": mt5.ORDER_TYPE_SELL_LIMIT,
                        "BUY_STOP": mt5.ORDER_TYPE_BUY_STOP,
                        "SELL_STOP": mt5.ORDER_TYPE_SELL_STOP,
                    }

                    request = {
                        "action": action,
                        "symbol": symbol,
                        "volume": float(volume),
                        "type": type_dict.get(order_type, mt5.ORDER_TYPE_BUY),
                        "price": float(curr_price),
                        "sl": float(stop_loss) if stop_loss else 0.0,
                        "tp": float(take_profit) if take_profit else 0.0,
                        "deviation": 20,
                        "magic": magic,
                        "comment": comment,
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }

                    result = mt5.order_send(request)
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        ticket = result.order or result.deal
                        logger.info(f"[NATIVE MT5 EXECUTION] {order_type} {volume} {symbol} @ {curr_price:.5f} -> Ticket: {ticket}")

                        from database.connection import db_manager as current_db
                        with current_db.get_session() as session:
                            trade_repo = TradeRepository(session)
                            trade_repo.create(
                                ticket=ticket,
                                symbol=symbol,
                                order_type=order_type,
                                volume=volume,
                                open_price=curr_price,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                status=TradeStatus.OPEN.value,
                                magic_number=magic,
                                comment=comment
                            )

                        return True, ticket, "Order executed successfully"
                    else:
                        retcode = result.retcode if result else "None"
                        logger.warning(f"Order attempt {attempt}/{self.max_retries} failed for {symbol}. Retcode: {retcode}")

            except Exception as e:
                logger.error(f"Error during order execution attempt {attempt}: {e}")

            time.sleep(self.retry_delay)

        return False, None, f"Order execution failed after {self.max_retries} attempts"

    def modify_order(self, ticket: int, stop_loss: Optional[float], take_profit: Optional[float]) -> Tuple[bool, str]:
        """Modifies Stop Loss and Take Profit of an existing order."""
        from database.connection import db_manager as current_db
        with current_db.get_session() as session:
            trade_repo = TradeRepository(session)
            trade = trade_repo.get_by_ticket(ticket)
            if not trade:
                return False, f"Trade with ticket {ticket} not found in database."

            trade_repo.update_trade(ticket, stop_loss=stop_loss, take_profit=take_profit)

        if not mt5_client.is_simulated and mt5_client.is_connected:
            mt5 = mt5_client.driver
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": float(stop_loss) if stop_loss else 0.0,
                "tp": float(take_profit) if take_profit else 0.0,
            }
            res = mt5.order_send(request)
            if not res or res.retcode != mt5.TRADE_RETCODE_DONE:
                return False, f"MT5 order modification failed: {res.comment if res else 'Unknown'}"

        logger.info(f"Order {ticket} modified successfully: SL={stop_loss}, TP={take_profit}")
        return True, "Order modified successfully"

    def close_trade(self, ticket: int, exit_reason: str = "MANUAL_CLOSE") -> Tuple[bool, str]:
        """Closes position completely."""
        from database.connection import db_manager as current_db

        symbol = ""
        close_price = 0.0
        profit = 0.0

        with current_db.get_session() as session:
            trade_repo = TradeRepository(session)
            trade = trade_repo.get_by_ticket(ticket)
            if not trade or trade.status != TradeStatus.OPEN.value:
                return False, f"Trade {ticket} is not open."

            symbol = str(trade.symbol)
            order_type = str(trade.order_type)
            open_price = float(trade.open_price)
            volume = float(trade.volume)

            tick = mt5_client.get_tick(symbol)
            close_price = tick.bid if order_type == "BUY" else (tick.ask if tick else open_price)

            pnl_mult = 1 if order_type == "BUY" else -1
            profit = (close_price - open_price) * pnl_mult * volume * 100000.0

            trade_repo.close_trade(ticket, close_price=close_price, profit=profit, exit_reason=exit_reason)

        logger.info(f"Closed trade {ticket} ({symbol}) @ {close_price:.5f}. Profit: ${profit:.2f}. Reason: {exit_reason}")
        return True, f"Closed trade {ticket} successfully"


execution_engine = ExecutionEngine()
