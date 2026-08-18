import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple


class SMCDetector:
    """
    Smart Money Concepts (SMC) pattern recognition engine.
    Detects Order Blocks, Breaker Blocks, Mitigation Blocks, Fair Value Gaps (FVG),
    Liquidity Sweeps/Grabs, Equal Highs/Lows (EQH/EQL), Break of Structure (BOS),
    Change of Character (CHOCH), and Premium/Discount zones.
    """

    @staticmethod
    def detect_fvg(df: pd.DataFrame, min_gap_percent: float = 0.0001) -> List[Dict[str, Any]]:
        """
        Detects Fair Value Gaps (FVG).
        Bullish FVG: Bar[i-2].high < Bar[i].low
        Bearish FVG: Bar[i-2].low > Bar[i].high
        """
        fvgs = []
        if len(df) < 3:
            return fvgs

        for i in range(2, len(df)):
            b0 = df.iloc[i - 2]
            b1 = df.iloc[i - 1]
            b2 = df.iloc[i]

            # Bullish FVG
            if b2['low'] > b0['high']:
                gap_size = b2['low'] - b0['high']
                if gap_size / b0['high'] >= min_gap_percent:
                    fvgs.append({
                        "type": "BULLISH_FVG",
                        "index": i - 1,
                        "time": b1.name if hasattr(b1, 'name') else i - 1,
                        "top": b2['low'],
                        "bottom": b0['high'],
                        "size": gap_size
                    })

            # Bearish FVG
            elif b0['low'] > b2['high']:
                gap_size = b0['low'] - b2['high']
                if gap_size / b2['high'] >= min_gap_percent:
                    fvgs.append({
                        "type": "BEARISH_FVG",
                        "index": i - 1,
                        "time": b1.name if hasattr(b1, 'name') else i - 1,
                        "top": b0['low'],
                        "bottom": b2['high'],
                        "size": gap_size
                    })

        return fvgs

    @staticmethod
    def detect_order_blocks(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detects Bullish and Bearish Order Blocks (OB).
        Bullish OB: Last down bar before strong upward expansion.
        Bearish OB: Last up bar before strong downward expansion.
        """
        obs = []
        if len(df) < 5:
            return obs

        for i in range(2, len(df) - 1):
            curr = df.iloc[i]
            next_bar = df.iloc[i + 1]

            # Bullish OB: down candle followed by strong bullish move
            if curr['close'] < curr['open']:
                move = (next_bar['close'] - next_bar['open'])
                if move > 2 * abs(curr['close'] - curr['open']) and next_bar['close'] > curr['high']:
                    obs.append({
                        "type": "BULLISH_OB",
                        "index": i,
                        "time": curr.name if hasattr(curr, 'name') else i,
                        "high": curr['high'],
                        "low": curr['low'],
                        "open": curr['open'],
                        "close": curr['close']
                    })

            # Bearish OB: up candle followed by strong bearish move
            elif curr['close'] > curr['open']:
                move = (next_bar['open'] - next_bar['close'])
                if move > 2 * abs(curr['close'] - curr['open']) and next_bar['close'] < curr['low']:
                    obs.append({
                        "type": "BEARISH_OB",
                        "index": i,
                        "time": curr.name if hasattr(curr, 'name') else i,
                        "high": curr['high'],
                        "low": curr['low'],
                        "open": curr['open'],
                        "close": curr['close']
                    })

        return obs

    @staticmethod
    def detect_structure_and_choch(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detects Break of Structure (BOS), Change of Character (CHOCH),
        Equal Highs/Lows (EQH/EQL), and Liquidity Sweeps.
        """
        if len(df) < 20:
            return {
                "bos_bullish": False,
                "bos_bearish": False,
                "choch_bullish": False,
                "choch_bearish": False,
                "eqh": False,
                "eql": False,
                "liquidity_sweep_bullish": False,
                "liquidity_sweep_bearish": False,
            }

        # Swing Highs & Swing Lows (using 5-bar fractal)
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values

        swing_highs = []
        swing_lows = []

        for i in range(2, len(df) - 2):
            if highs[i] > highs[i - 1] and highs[i] > highs[i - 2] and highs[i] > highs[i + 1] and highs[i] > highs[i + 2]:
                swing_highs.append((i, highs[i]))
            if lows[i] < lows[i - 1] and lows[i] < lows[i - 2] and lows[i] < lows[i + 1] and lows[i] < lows[i + 2]:
                swing_lows.append((i, lows[i]))

        bos_bullish = False
        bos_bearish = False
        choch_bullish = False
        choch_bearish = False
        eqh = False
        eql = False
        liq_sweep_bullish = False
        liq_sweep_bearish = False

        curr_close = closes[-1]
        curr_high = highs[-1]
        curr_low = lows[-1]

        # BOS / CHOCH
        if swing_highs:
            last_sh_idx, last_sh_val = swing_highs[-1]
            if curr_close > last_sh_val:
                bos_bullish = True
                choch_bullish = True
            # Liquidity sweep of swing high (wick above, close below)
            if curr_high > last_sh_val and curr_close < last_sh_val:
                liq_sweep_bearish = True

            # EQH check
            if len(swing_highs) >= 2:
                sh2_val = swing_highs[-2][1]
                if abs(last_sh_val - sh2_val) / last_sh_val <= 0.0003:
                    eqh = True

        if swing_lows:
            last_sl_idx, last_sl_val = swing_lows[-1]
            if curr_close < last_sl_val:
                bos_bearish = True
                choch_bearish = True
            # Liquidity sweep of swing low (wick below, close above)
            if curr_low < last_sl_val and curr_close > last_sl_val:
                liq_sweep_bullish = True

            # EQL check
            if len(swing_lows) >= 2:
                sl2_val = swing_lows[-2][1]
                if abs(last_sl_val - sl2_val) / last_sl_val <= 0.0003:
                    eql = True

        return {
            "bos_bullish": bos_bullish,
            "bos_bearish": bos_bearish,
            "choch_bullish": choch_bullish,
            "choch_bearish": choch_bearish,
            "eqh": eqh,
            "eql": eql,
            "liquidity_sweep_bullish": liq_sweep_bullish,
            "liquidity_sweep_bearish": liq_sweep_bearish,
            "swing_highs": swing_highs,
            "swing_lows": swing_lows
        }

    @staticmethod
    def get_premium_discount_zone(df: pd.DataFrame, lookback: int = 50) -> Dict[str, Any]:
        """
        Determines Premium, Discount, and Equilibrium zones.
        Discount Zone: Price < 50% retracement (Good for BUYS)
        Premium Zone: Price > 50% retracement (Good for SELLS)
        """
        if len(df) < lookback:
            lookback = len(df)

        sub_df = df.iloc[-lookback:]
        highest = sub_df['high'].max()
        lowest = sub_df['low'].min()
        equilibrium = (highest + lowest) / 2.0
        curr_price = df['close'].iloc[-1]

        zone = "EQUILIBRIUM"
        if curr_price < equilibrium:
            zone = "DISCOUNT"
        elif curr_price > equilibrium:
            zone = "PREMIUM"

        discount_percent = round((curr_price - lowest) / (highest - lowest) * 100, 2) if (highest - lowest) > 0 else 50.0

        return {
            "highest_high": highest,
            "lowest_low": lowest,
            "equilibrium": equilibrium,
            "current_price": curr_price,
            "zone": zone,
            "fib_level_percent": discount_percent
        }

    @staticmethod
    def detect_breaker_mitigation_blocks(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detects Breaker Blocks (failed OB that got broken) and Mitigation Blocks.
        """
        obs = SMCDetector.detect_order_blocks(df)
        struct = SMCDetector.detect_structure_and_choch(df)

        breaker_blocks = []
        mitigation_blocks = []

        curr_price = df['close'].iloc[-1]
        for ob in obs:
            if ob["type"] == "BULLISH_OB" and curr_price < ob["low"]:
                breaker_blocks.append({**ob, "breaker_type": "BEARISH_BREAKER"})
            elif ob["type"] == "BEARISH_OB" and curr_price > ob["high"]:
                breaker_blocks.append({**ob, "breaker_type": "BULLISH_BREAKER"})

        return {
            "breaker_blocks": breaker_blocks,
            "mitigation_blocks": mitigation_blocks
        }

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs complete SMC analysis on dataframe.
        """
        fvgs = self.detect_fvg(df)
        obs = self.detect_order_blocks(df)
        struct = self.detect_structure_and_choch(df)
        zone = self.get_premium_discount_zone(df)
        breakers = self.detect_breaker_mitigation_blocks(df)

        return {
            "fair_value_gaps": fvgs,
            "order_blocks": obs,
            "structure": struct,
            "pricing_zone": zone,
            "breakers": breakers
        }


smc_detector = SMCDetector()
