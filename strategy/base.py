from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Dict, Any
from signals.models import SignalOutput


class BaseStrategy(ABC):
    """
    Abstract Base Strategy Interface.
    All trading strategies must inherit from this class and implement the `analyze` method.
    """

    def __init__(self, name: str, timeframe: str = "H1"):
        self.name = name
        self.timeframe = timeframe

    @abstractmethod
    def analyze(self, symbol: str, df: pd.DataFrame, df_daily: Optional[pd.DataFrame] = None) -> SignalOutput:
        """
        Analyzes market data and returns a structured SignalOutput object.
        """
        pass
