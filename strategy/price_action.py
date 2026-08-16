import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


class PriceActionDetector:
    """
    Price Action pattern detector for candlestick & chart structure signals:
    Pin Bar, Hammer, Shooting Star, Bullish/Bearish Engulfing, Inside Bar,
    Outside Bar, Breakout, Retest, and Trend Continuation.
    """

    @staticmethod
    def detect_patterns(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyzes the latest bars in df and returns pattern flags and score adjustments.
        """
        if len(df) < 5:
            return {}

        c = df.iloc[-1]
        p = df.iloc[-2]
        p2 = df.iloc[-3]

        open_c, high_c, low_c, close_c = c['open'], c['high'], c['low'], c['close']
        open_p, high_p, low_p, close_p = p['open'], p['high'], p['low'], p['close']

        body_c = abs(close_c - open_c)
        range_c = high_c - low_c if (high_c - low_c) > 0 else 0.00001
        upper_wick = high_c - max(open_c, close_c)
        lower_wick = min(open_c, close_c) - low_c

        body_p = abs(close_p - open_p)
        range_p = high_p - low_p if (high_p - low_p) > 0 else 0.00001

        patterns = {
            "pin_bar_bullish": False,
            "pin_bar_bearish": False,
            "hammer": False,
            "shooting_star": False,
            "engulfing_bullish": False,
            "engulfing_bearish": False,
            "inside_bar": False,
            "outside_bar": False,
            "breakout_bullish": False,
            "breakout_bearish": False,
            "retest": False,
            "trend_continuation_bullish": False,
            "trend_continuation_bearish": False,
        }

        # Pin Bar
        if lower_wick >= 2 * body_c and upper_wick <= body_c:
            patterns["pin_bar_bullish"] = True
            patterns["hammer"] = True
        elif upper_wick >= 2 * body_c and lower_wick <= body_c:
            patterns["pin_bar_bearish"] = True
            patterns["shooting_star"] = True

        # Engulfing
        if close_c > open_c and close_p < open_p and close_c >= open_p and open_c <= close_p:
            patterns["engulfing_bullish"] = True
        elif close_c < open_c and close_p > open_p and close_c <= open_p and open_c >= close_p:
            patterns["engulfing_bearish"] = True

        # Inside Bar
        if high_c <= high_p and low_c >= low_p:
            patterns["inside_bar"] = True

        # Outside Bar
        if high_c >= high_p and low_c <= low_p:
            patterns["outside_bar"] = True

        # Breakout (Crossing 20-period Donchian High/Low)
        recent_high_20 = df['high'].iloc[-21:-1].max() if len(df) >= 21 else df['high'].max()
        recent_low_20 = df['low'].iloc[-21:-1].min() if len(df) >= 21 else df['low'].min()

        if close_c > recent_high_20:
            patterns["breakout_bullish"] = True
        elif close_c < recent_low_20:
            patterns["breakout_bearish"] = True

        # Retest (Price touched broken level and rejected)
        if patterns["breakout_bullish"] or close_p > recent_high_20:
            if low_c <= recent_high_20 and close_c > recent_high_20:
                patterns["retest"] = True

        # Trend Continuation (3 consecutive higher closes or lower closes with higher/lower lows)
        if len(df) >= 4:
            c1, c2, c3 = df['close'].iloc[-1], df['close'].iloc[-2], df['close'].iloc[-3]
            if c1 > c2 > c3:
                patterns["trend_continuation_bullish"] = True
            elif c1 < c2 < c3:
                patterns["trend_continuation_bearish"] = True

        return patterns


price_action_detector = PriceActionDetector()
