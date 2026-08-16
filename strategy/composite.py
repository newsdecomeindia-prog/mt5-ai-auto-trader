import pandas as pd
from typing import Optional
from strategy.base import BaseStrategy
from signals.models import SignalOutput


class CompositeAIStrategy(BaseStrategy):
    """
    Composite AI Strategy integrating Technical Indicators, Price Action, SMC, and ICT.
    """

    def __init__(self, timeframe: str = "H1"):
        super().__init__(name="Composite_AI_SMC_ICT_Strategy", timeframe=timeframe)

    def analyze(self, symbol: str, df: pd.DataFrame, df_daily: Optional[pd.DataFrame] = None) -> SignalOutput:
        from signals.engine import signal_engine
        return signal_engine.generate_signal(
            symbol=symbol,
            df=df,
            timeframe=self.timeframe,
            df_daily=df_daily
        )


composite_ai_strategy = CompositeAIStrategy()
