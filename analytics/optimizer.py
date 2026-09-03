import pandas as pd
from typing import Dict, Any, List
from analytics.backtester import Backtester
from core import get_logger

logger = get_logger("general")


class StrategyOptimizer:
    """
    Walk-Forward Testing and Strategy Parameter Optimization Engine.
    """

    def walk_forward_test(
        self,
        symbol: str,
        df: pd.DataFrame,
        in_sample_ratio: float = 0.7
    ) -> Dict[str, Any]:
        """
        Splits data into In-Sample (training/fitting) and Out-Of-Sample (testing) sets.
        """
        split_idx = int(len(df) * in_sample_ratio)
        df_in_sample = df.iloc[:split_idx]
        df_out_sample = df.iloc[split_idx:]

        bt = Backtester()
        res_in = bt.run(symbol, df_in_sample)
        res_out = bt.run(symbol, df_out_sample)

        return {
            "in_sample": res_in,
            "out_of_sample": res_out,
            "efficiency_ratio": round(res_out.get("win_rate", 0) / (res_in.get("win_rate", 1) or 1), 2)
        }


strategy_optimizer = StrategyOptimizer()
