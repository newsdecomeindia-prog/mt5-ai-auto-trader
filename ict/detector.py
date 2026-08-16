import pandas as pd
import numpy as np
from datetime import datetime, time, timezone
from typing import Dict, Any, List, Optional, Tuple


class ICTDetector:
    """
    Inner Circle Trader (ICT) concepts detector engine:
    OTE (Optimal Trade Entry), Kill Zones, Power Of Three (AMD),
    Judas Swing, Liquidity Pools (BSL/SSL), and Daily Bias.
    """

    # Kill Zones in UTC
    KILL_ZONES = {
        "ASIAN": (time(0, 0), time(4, 0)),
        "LONDON": (time(7, 0), time(10, 0)),
        "NEW_YORK": (time(12, 0), time(15, 0)),
        "LONDON_CLOSE": (time(15, 0), time(17, 0))
    }

    @staticmethod
    def get_current_kill_zone(current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Determines active ICT Kill Zone.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        current_t = current_time.time() if hasattr(current_time, "time") else time(12, 0)
        active_zone = "OUTSIDE_KILL_ZONE"
        is_active = False

        for zone_name, (start_t, end_t) in ICTDetector.KILL_ZONES.items():
            if start_t <= current_t <= end_t:
                active_zone = zone_name
                is_active = True
                break

        return {
            "active_zone": active_zone,
            "is_kill_zone_active": is_active,
            "utc_time": current_time.strftime("%H:%M:%S") if hasattr(current_time, "strftime") else "12:00:00"
        }

    @staticmethod
    def calculate_ote(df: pd.DataFrame, lookback: int = 40) -> Dict[str, Any]:
        """
        Calculates Optimal Trade Entry (OTE) Fibonacci levels (61.8%, 70.5%, 79.0%).
        """
        if len(df) < lookback:
            lookback = len(df)

        sub_df = df.iloc[-lookback:]
        high = sub_df['high'].max()
        low = sub_df['low'].min()
        curr_price = df['close'].iloc[-1]
        range_diff = high - low if (high - low) > 0 else 0.00001

        # Fibonacci Retracements from swing
        fib_618 = high - 0.618 * range_diff
        fib_705 = high - 0.705 * range_diff  # Sweet spot
        fib_790 = high - 0.790 * range_diff

        in_ote_bullish = fib_790 <= curr_price <= fib_618
        in_ote_bearish = (high - 0.210 * range_diff) <= curr_price <= (high - 0.382 * range_diff)

        return {
            "swing_high": high,
            "swing_low": low,
            "fib_618": round(fib_618, 5),
            "fib_705": round(fib_705, 5),
            "fib_790": round(fib_790, 5),
            "in_ote_bullish": in_ote_bullish,
            "in_ote_bearish": in_ote_bearish
        }

    @staticmethod
    def detect_liquidity_pools(df: pd.DataFrame, lookback: int = 50) -> Dict[str, Any]:
        """
        Identifies Buy Side Liquidity (BSL) above key highs and
        Sell Side Liquidity (SSL) below key lows.
        """
        if len(df) < lookback:
            lookback = len(df)

        sub_df = df.iloc[-lookback:]
        bsl_price = sub_df['high'].max()
        ssl_price = sub_df['low'].min()
        curr_price = df['close'].iloc[-1]

        dist_to_bsl_pips = round(abs(bsl_price - curr_price) * 10000, 1)
        dist_to_ssl_pips = round(abs(curr_price - ssl_price) * 10000, 1)

        return {
            "buy_side_liquidity": bsl_price,
            "sell_side_liquidity": ssl_price,
            "distance_to_bsl_pips": dist_to_bsl_pips,
            "distance_to_ssl_pips": dist_to_ssl_pips
        }

    @staticmethod
    def detect_judas_swing(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detects Judas Swing (False move in Kill Zone before true trend expansion).
        Example: Price drops sharply at London open to sweep SSL before rallying hard up.
        """
        if len(df) < 10:
            return {"judas_swing_bullish": False, "judas_swing_bearish": False}

        c = df.iloc[-1]
        p = df.iloc[-2]
        p2 = df.iloc[-3]

        kz_info = ICTDetector.get_current_kill_zone()

        judas_bullish = False
        judas_bearish = False

        if kz_info["is_kill_zone_active"]:
            # Rapid drop followed by strong reversal candle
            if p['close'] < p['open'] and c['close'] > c['open'] and c['close'] > p['high']:
                judas_bullish = True
            # Rapid rise followed by strong reversal candle
            elif p['close'] > p['open'] and c['close'] < c['open'] and c['close'] < p['low']:
                judas_bearish = True

        return {
            "judas_swing_bullish": judas_bullish,
            "judas_swing_bearish": judas_bearish,
            "active_kill_zone": kz_info["active_zone"]
        }

    @staticmethod
    def detect_power_of_three(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Power Of Three (AMD - Accumulation, Manipulation, Distribution).
        Analyzes session candle structure.
        """
        if len(df) < 20:
            return {"phase": "ACCUMULATION", "confidence": 50.0}

        closes = df['close'].tail(20)
        returns = closes.pct_change().dropna()
        volatility = returns.std()

        curr_return = returns.iloc[-1] if not returns.empty else 0.0

        if volatility < 0.0005:
            phase = "ACCUMULATION"
        elif abs(curr_return) > 2 * volatility:
            phase = "MANIPULATION"
        else:
            phase = "DISTRIBUTION"

        return {
            "phase": phase,
            "volatility": round(volatility, 6)
        }

    @staticmethod
    def determine_daily_bias(df_daily: pd.DataFrame) -> Dict[str, Any]:
        """
        Determines Daily Bias (BULLISH, BEARISH, or NEUTRAL) using daily market structure.
        """
        if len(df_daily) < 5:
            return {"bias": "NEUTRAL", "confidence": 50.0}

        d_close = df_daily['close'].iloc[-1]
        d_prev_close = df_daily['close'].iloc[-2]
        sma_20 = df_daily['close'].rolling(20).mean().iloc[-1] if len(df_daily) >= 20 else d_close

        if d_close > d_prev_close and d_close > sma_20:
            bias = "BULLISH"
            confidence = 80.0
        elif d_close < d_prev_close and d_close < sma_20:
            bias = "BEARISH"
            confidence = 80.0
        else:
            bias = "NEUTRAL"
            confidence = 50.0

        return {
            "bias": bias,
            "confidence": confidence,
            "last_close": d_close,
            "sma_20": round(sma_20, 5)
        }

    def analyze(self, df: pd.DataFrame, df_daily: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Full ICT analysis report.
        """
        kz = self.get_current_kill_zone()
        ote = self.calculate_ote(df)
        pools = self.detect_liquidity_pools(df)
        judas = self.detect_judas_swing(df)
        amd = self.detect_power_of_three(df)
        bias = self.determine_daily_bias(df_daily) if df_daily is not None else {"bias": "NEUTRAL", "confidence": 50.0}

        return {
            "kill_zone": kz,
            "ote": ote,
            "liquidity_pools": pools,
            "judas_swing": judas,
            "power_of_three": amd,
            "daily_bias": bias
        }


ict_detector = ICTDetector()
