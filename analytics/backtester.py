import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from strategy import composite_ai_strategy
from database import Trade, TradeStatus
from analytics.metrics import performance_analytics
from core import get_logger

logger = get_logger("general")


class Backtester:
    """
    Historical backtesting engine with realistic bar-by-bar simulation,
    spread, slippage, and position tracking.
    """

    def __init__(self, initial_balance: float = 10000.0, spread_pips: float = 1.0, slippage_pips: float = 0.5):
        self.initial_balance = initial_balance
        self.spread_pips = spread_pips
        self.slippage_pips = slippage_pips

    def run(self, symbol: str, df: pd.DataFrame, timeframe: str = "H1") -> Dict[str, Any]:
        """
        Runs backtest across historical dataframe.
        """
        if len(df) < 50:
            return {"error": "Insufficient historical data for backtesting"}

        point = 0.0001 if "JPY" not in symbol else 0.01
        spread_val = self.spread_pips * point
        slippage_val = self.slippage_pips * point

        closed_trades: List[Trade] = []
        open_position = None
        ticket_counter = 1

        for i in range(40, len(df)):
            sub_df = df.iloc[:i]
            c_bar = df.iloc[i]
            curr_price = c_bar['close']
            high_price = c_bar['high']
            low_price = c_bar['low']

            if open_position:
                sl = open_position["sl"]
                tp = open_position["tp"]
                o_type = open_position["type"]

                hit_sl = False
                hit_tp = False

                if o_type == "BUY":
                    if low_price <= sl:
                        hit_sl = True
                    elif high_price >= tp:
                        hit_tp = True
                elif o_type == "SELL":
                    if high_price >= sl:
                        hit_sl = True
                    elif low_price <= tp:
                        hit_tp = True

                if hit_sl or hit_tp:
                    exit_price = sl if hit_sl else tp
                    pnl_mult = 1 if o_type == "BUY" else -1
                    profit = (exit_price - open_position["entry"]) * pnl_mult * open_position["volume"] * 100000.0

                    t = Trade(
                        ticket=open_position["ticket"],
                        symbol=symbol,
                        order_type=o_type,
                        volume=open_position["volume"],
                        open_price=open_position["entry"],
                        close_price=exit_price,
                        stop_loss=sl,
                        take_profit=tp,
                        profit=profit,
                        status=TradeStatus.CLOSED.value,
                        exit_reason="SL_HIT" if hit_sl else "TP_HIT"
                    )
                    closed_trades.append(t)
                    open_position = None

            if open_position is None:
                sig = composite_ai_strategy.analyze(symbol, sub_df)
                if sig.signal_type in ("BUY", "SELL") and sig.scores.confidence_score >= 60.0:
                    entry = curr_price + (spread_val + slippage_val if sig.signal_type == "BUY" else -(spread_val + slippage_val))
                    open_position = {
                        "ticket": ticket_counter,
                        "type": sig.signal_type,
                        "entry": entry,
                        "sl": sig.stop_loss or (entry - 0.0050 if sig.signal_type == "BUY" else entry + 0.0050),
                        "tp": sig.take_profit or (entry + 0.0100 if sig.signal_type == "BUY" else entry - 0.0100),
                        "volume": 0.1
                    }
                    ticket_counter += 1

        metrics = performance_analytics.calculate_trade_metrics(closed_trades)
        metrics["symbol"] = symbol
        metrics["timeframe"] = timeframe
        return metrics


backtester = Backtester()
