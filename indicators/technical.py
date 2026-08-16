import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


class TechnicalIndicators:
    """
    Production technical indicators suite implemented in pure NumPy and Pandas.
    Supports EMA, SMA, RSI, MACD, ADX, ATR, VWAP, CCI, Momentum, Stochastic,
    SuperTrend, Bollinger Bands, Ichimoku, and Donchian Channel.
    """

    @staticmethod
    def sma(series: pd.Series, period: int = 14) -> pd.Series:
        return series.rolling(window=period).mean()

    @staticmethod
    def ema(series: pd.Series, period: int = 14) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss.replace(0, np.nan))
        rsi_val = 100 - (100 / (1 + rs))
        return rsi_val.fillna(50)

    @staticmethod
    def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        fast_ema = TechnicalIndicators.ema(series, fast)
        slow_ema = TechnicalIndicators.ema(series, slow)
        macd_line = fast_ema - slow_ema
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df['high']
        low = df['low']

        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        atr_series = TechnicalIndicators.atr(df, period)
        plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(period).mean() / atr_series.replace(0, np.nan))
        minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(period).mean() / atr_series.replace(0, np.nan))

        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        return dx.rolling(window=period).mean().fillna(0)

    @staticmethod
    def vwap(df: pd.DataFrame) -> pd.Series:
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        volume = df['tick_volume'] if 'tick_volume' in df.columns else df.get('real_volume', pd.Series(1, index=df.index))
        cumulative_tp_v = (typical_price * volume).cumsum()
        cumulative_v = volume.cumsum()
        return cumulative_tp_v / cumulative_v.replace(0, np.nan)

    @staticmethod
    def cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
        cci_val = (typical_price - sma_tp) / (0.015 * mean_deviation.replace(0, np.nan))
        return cci_val.fillna(0)

    @staticmethod
    def momentum(series: pd.Series, period: int = 14) -> pd.Series:
        return series - series.shift(period)

    @staticmethod
    def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        k_percent = 100 * ((df['close'] - low_min) / (high_max - low_min).replace(0, np.nan))
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent.fillna(50), d_percent.fillna(50)

    @staticmethod
    def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
        atr_series = TechnicalIndicators.atr(df, period)
        hl2 = (df['high'] + df['low']) / 2
        basic_upperband = hl2 + (multiplier * atr_series)
        basic_lowerband = hl2 - (multiplier * atr_series)

        upperband = basic_upperband.copy()
        lowerband = basic_lowerband.copy()
        supertrend = pd.Series(0.0, index=df.index)
        direction = pd.Series(1, index=df.index)

        close = df['close']
        for i in range(1, len(df)):
            if basic_upperband.iloc[i] < upperband.iloc[i - 1] or close.iloc[i - 1] > upperband.iloc[i - 1]:
                upperband.iloc[i] = basic_upperband.iloc[i]
            else:
                upperband.iloc[i] = upperband.iloc[i - 1]

            if basic_lowerband.iloc[i] > lowerband.iloc[i - 1] or close.iloc[i - 1] < lowerband.iloc[i - 1]:
                lowerband.iloc[i] = basic_lowerband.iloc[i]
            else:
                lowerband.iloc[i] = lowerband.iloc[i - 1]

            if supertrend.iloc[i - 1] == upperband.iloc[i - 1]:
                if close.iloc[i] > upperband.iloc[i]:
                    supertrend.iloc[i] = lowerband.iloc[i]
                    direction.iloc[i] = 1
                else:
                    supertrend.iloc[i] = upperband.iloc[i]
                    direction.iloc[i] = -1
            else:
                if close.iloc[i] < lowerband.iloc[i]:
                    supertrend.iloc[i] = upperband.iloc[i]
                    direction.iloc[i] = -1
                else:
                    supertrend.iloc[i] = lowerband.iloc[i]
                    direction.iloc[i] = 1

        return supertrend, direction

    @staticmethod
    def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        middle = TechnicalIndicators.sma(series, period)
        std = series.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    @staticmethod
    def ichimoku(df: pd.DataFrame, tenkan_period: int = 9, kijun_period: int = 26, senkou_b_period: int = 52) -> Dict[str, pd.Series]:
        tenkan_sen = (df['high'].rolling(window=tenkan_period).max() + df['low'].rolling(window=tenkan_period).min()) / 2
        kijun_sen = (df['high'].rolling(window=kijun_period).max() + df['low'].rolling(window=kijun_period).min()) / 2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
        senkou_span_b = ((df['high'].rolling(window=senkou_b_period).max() + df['low'].rolling(window=senkou_b_period).min()) / 2).shift(kijun_period)
        chikou_span = df['close'].shift(-kijun_period)

        return {
            "tenkan_sen": tenkan_sen,
            "kijun_sen": kijun_sen,
            "senkou_span_a": senkou_span_a,
            "senkou_span_b": senkou_span_b,
            "chikou_span": chikou_span
        }

    @staticmethod
    def donchian_channel(df: pd.DataFrame, period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
        upper = df['high'].rolling(window=period).max()
        lower = df['low'].rolling(window=period).min()
        middle = (upper + lower) / 2
        return upper, middle, lower


technical_indicators = TechnicalIndicators()
