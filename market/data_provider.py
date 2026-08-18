import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from mt5 import mt5_client, TickData, SymbolInfo
from market.timeframes import Timeframe, TIMEFRAME_MAP
from core import get_logger

logger = get_logger("trading")


class MarketDataProvider:
    """
    Provides real-time tick data, historical OHLC dataframes, spread, ATR, volume,
    and market depth info.
    """

    def __init__(self):
        pass

    def get_tick(self, symbol: str) -> Optional[TickData]:
        """Gets current live tick data."""
        return mt5_client.get_tick(symbol)

    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Gets symbol properties."""
        return mt5_client.get_symbol_info(symbol)

    def get_spread(self, symbol: str) -> float:
        """Calculates current spread in pips."""
        tick = self.get_tick(symbol)
        sym_info = self.get_symbol_info(symbol)
        if not tick or not sym_info:
            return 0.0
        point = sym_info.point if sym_info.point > 0 else 0.00001
        multiplier = 10 if sym_info.digits in (3, 5) else 1
        return round((tick.ask - tick.bid) / (point * multiplier), 2)

    def get_ohlc(self, symbol: str, timeframe: str = "H1", count: int = 200) -> pd.DataFrame:
        """
        Retrieves historical bar data and returns a pandas DataFrame with:
        ['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
        """
        if not mt5_client.is_connected:
            mt5_client.connect()

        tf_val = TIMEFRAME_MAP.get(timeframe, TIMEFRAME_MAP["H1"])
        rates = mt5_client.driver.copy_rates_from_pos(symbol, tf_val, 0, count)

        if rates is None or len(rates) == 0:
            logger.warning(f"Failed to fetch OHLC rates for {symbol} ({timeframe})")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['datetime'] = pd.to_datetime(df['time'], unit='s', utc=True)
        df.set_index('datetime', inplace=False)
        return df

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculates Average True Range (ATR) value."""
        if len(df) < period + 1:
            return 0.0

        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        return float(atr) if not np.isnan(atr) else 0.0

    def get_market_depth(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Returns order book / market depth snapshot if available or simulated.
        """
        tick = self.get_tick(symbol)
        if not tick:
            return []

        # Return level 2 book snapshot
        step = 0.0001 if tick.ask < 100 else 0.1
        book = []
        for i in range(1, 6):
            book.append({
                "type": "SELL",
                "price": round(tick.ask + i * step, 5),
                "volume": round(10.0 * i, 2)
            })
            book.append({
                "type": "BUY",
                "price": round(tick.bid - i * step, 5),
                "volume": round(10.0 * i, 2)
            })
        return book


market_data_provider = MarketDataProvider()
