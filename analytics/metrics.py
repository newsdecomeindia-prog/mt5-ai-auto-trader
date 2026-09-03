import math
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from database import Trade, TradeStatus


class PerformanceAnalytics:
    """
    Calculates quantitative performance metrics: Win Rate, Loss Rate, Profit Factor,
    Average Win, Average Loss, Expectancy, Maximum Drawdown, and Equity Curve.
    """

    @staticmethod
    def calculate_trade_metrics(trades: List[Trade]) -> Dict[str, Any]:
        """Calculates performance statistics from a list of closed Trade objects."""
        closed_trades = [t for t in trades if t.status == TradeStatus.CLOSED.value]
        total_trades = len(closed_trades)

        if total_trades == 0:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "loss_rate": 0.0,
                "total_profit": 0.0,
                "profit_factor": 0.0,
                "average_win": 0.0,
                "average_loss": 0.0,
                "expectancy": 0.0,
                "max_drawdown": 0.0,
                "equity_curve": []
            }

        profits = [t.profit for t in closed_trades]
        winning_trades = [p for p in profits if p > 0]
        losing_trades = [p for p in profits if p <= 0]

        num_wins = len(winning_trades)
        num_losses = len(losing_trades)

        win_rate = round((num_wins / total_trades) * 100.0, 2)
        loss_rate = round((num_losses / total_trades) * 100.0, 2)

        gross_profit = sum(winning_trades)
        gross_loss = abs(sum(losing_trades))

        total_profit = round(sum(profits), 2)
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (round(gross_profit, 2) if gross_profit > 0 else 0.0)

        avg_win = round(gross_profit / num_wins, 2) if num_wins > 0 else 0.0
        avg_loss = round(gross_loss / num_losses, 2) if num_losses > 0 else 0.0

        expectancy = round(((win_rate / 100.0) * avg_win) - ((loss_rate / 100.0) * avg_loss), 2)

        equity = 10000.0
        equity_curve = [equity]
        peak = equity
        max_dd = 0.0

        for p in profits:
            equity += p
            equity_curve.append(round(equity, 2))
            if equity > peak:
                peak = equity
            dd = ((peak - equity) / peak) * 100.0 if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        return {
            "total_trades": total_trades,
            "winning_trades": num_wins,
            "losing_trades": num_losses,
            "win_rate": win_rate,
            "loss_rate": loss_rate,
            "total_profit": total_profit,
            "profit_factor": profit_factor,
            "average_win": avg_win,
            "average_loss": avg_loss,
            "expectancy": expectancy,
            "max_drawdown": round(max_dd, 2),
            "equity_curve": equity_curve
        }


performance_analytics = PerformanceAnalytics()
