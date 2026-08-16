import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from signals.models import SignalOutput, SignalScores
from indicators import technical_indicators
from strategy.price_action import price_action_detector
from smc import smc_detector
from ict import ict_detector
from core import get_logger

logger = get_logger("trading")


class SignalEngine:
    """
    Multi-factor AI Signal Generation Engine.
    Combines Technical Indicators, Price Action, SMC, ICT, Trend, Volatility, and Volume
    into clear BUY / SELL / NO_TRADE decisions with Confidence, Trade, and Probability Scores.
    """

    def generate_signal(self, symbol: str, df: pd.DataFrame, timeframe: str = "H1", df_daily: Optional[pd.DataFrame] = None) -> SignalOutput:
        """
        Processes dataframe and outputs structured SignalOutput.
        """
        now_utc = datetime.now(timezone.utc)
        if df.empty or len(df) < 30:
            return SignalOutput(
                symbol=symbol,
                timeframe=timeframe,
                signal_type="NO_TRADE",
                scores=SignalScores(confidence_score=0, trade_score=0, probability_score=0),
                created_at=now_utc
            )

        curr_price = df['close'].iloc[-1]
        high = df['high'].iloc[-1]
        low = df['low'].iloc[-1]

        # 1. Indicators
        rsi = technical_indicators.rsi(df['close']).iloc[-1]
        ema_20 = technical_indicators.ema(df['close'], 20).iloc[-1]
        ema_50 = technical_indicators.ema(df['close'], 50).iloc[-1]
        atr = technical_indicators.atr(df, 14).iloc[-1]
        adx = technical_indicators.adx(df, 14).iloc[-1]
        supertrend, st_dir = technical_indicators.supertrend(df)
        st_direction = st_dir.iloc[-1]

        # 2. Price Action
        pa_patterns = price_action_detector.detect_patterns(df)

        # 3. SMC
        smc_res = smc_detector.analyze(df)

        # 4. ICT
        ict_res = ict_detector.analyze(df, df_daily)

        # Scorer initialization
        bullish_points = 0
        bearish_points = 0
        total_max_points = 100

        # Trend & Moving Average Score (Max 20 pts)
        if curr_price > ema_20 > ema_50:
            bullish_points += 20
        elif curr_price < ema_20 < ema_50:
            bearish_points += 20

        # SuperTrend & ADX Volatility (Max 15 pts)
        if st_direction == 1 and adx >= 20:
            bullish_points += 15
        elif st_direction == -1 and adx >= 20:
            bearish_points += 15

        # RSI Momentum (Max 10 pts)
        if 40 <= rsi <= 65 and curr_price > ema_20:
            bullish_points += 10
        elif 35 <= rsi <= 60 and curr_price < ema_20:
            bearish_points += 10

        # Price Action Patterns (Max 15 pts)
        if pa_patterns.get("pin_bar_bullish") or pa_patterns.get("engulfing_bullish") or pa_patterns.get("breakout_bullish"):
            bullish_points += 15
        if pa_patterns.get("pin_bar_bearish") or pa_patterns.get("engulfing_bearish") or pa_patterns.get("breakout_bearish"):
            bearish_points += 15

        # SMC Confluence: Order Block + Discount/Premium (Max 20 pts)
        smc_zone = smc_res.get("pricing_zone", {}).get("zone", "EQUILIBRIUM")
        smc_struct = smc_res.get("structure", {})
        if smc_zone == "DISCOUNT" and (smc_struct.get("bos_bullish") or smc_struct.get("liquidity_sweep_bullish")):
            bullish_points += 20
        elif smc_zone == "PREMIUM" and (smc_struct.get("bos_bearish") or smc_struct.get("liquidity_sweep_bearish")):
            bearish_points += 20

        # ICT Confluence: Kill Zone + OTE + Daily Bias (Max 20 pts)
        ict_ote = ict_res.get("ote", {})
        ict_bias = ict_res.get("daily_bias", {}).get("bias", "NEUTRAL")
        ict_kz = ict_res.get("kill_zone", {}).get("is_kill_zone_active", False)

        if ict_ote.get("in_ote_bullish") and (ict_bias == "BULLISH" or ict_kz):
            bullish_points += 20
        elif ict_ote.get("in_ote_bearish") and (ict_bias == "BEARISH" or ict_kz):
            bearish_points += 20

        # Determine Signal Type and Scores
        signal_type = "NO_TRADE"
        conf_score = 0.0
        trade_score = 0.0
        prob_score = 0.0

        threshold = 60.0  # Minimum 60% confidence required for entry

        if bullish_points >= threshold and bullish_points > bearish_points:
            signal_type = "BUY"
            conf_score = min(100.0, float(bullish_points))
            trade_score = min(100.0, float(bullish_points * 0.95 + adx * 0.2))
            prob_score = min(100.0, float(conf_score * 0.85 + (100 if ict_kz else 50) * 0.15))

        elif bearish_points >= threshold and bearish_points > bullish_points:
            signal_type = "SELL"
            conf_score = min(100.0, float(bearish_points))
            trade_score = min(100.0, float(bearish_points * 0.95 + adx * 0.2))
            prob_score = min(100.0, float(conf_score * 0.85 + (100 if ict_kz else 50) * 0.15))

        # Stop Loss & Take Profit Calculation
        stop_loss = None
        take_profit = None
        rr_ratio = 0.0

        if signal_type == "BUY":
            sl_distance = max(1.5 * atr, 0.0015)
            stop_loss = round(curr_price - sl_distance, 5)
            take_profit = round(curr_price + 2.5 * sl_distance, 5)
            rr_ratio = 2.5

        elif signal_type == "SELL":
            sl_distance = max(1.5 * atr, 0.0015)
            stop_loss = round(curr_price + sl_distance, 5)
            take_profit = round(curr_price - 2.5 * sl_distance, 5)
            rr_ratio = 2.5

        scores = SignalScores(
            confidence_score=round(conf_score, 1),
            trade_score=round(trade_score, 1),
            probability_score=round(prob_score, 1)
        )

        return SignalOutput(
            symbol=symbol,
            timeframe=timeframe,
            signal_type=signal_type,
            scores=scores,
            entry_price=round(curr_price, 5),
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=rr_ratio,
            indicators={
                "rsi": round(rsi, 2),
                "ema_20": round(ema_20, 5),
                "ema_50": round(ema_50, 5),
                "atr": round(atr, 5),
                "adx": round(adx, 2),
                "supertrend_direction": int(st_direction)
            },
            price_action=pa_patterns,
            smc={
                "pricing_zone": smc_zone,
                "bos_bullish": smc_struct.get("bos_bullish", False),
                "bos_bearish": smc_struct.get("bos_bearish", False)
            },
            ict={
                "kill_zone_active": ict_kz,
                "daily_bias": ict_bias,
                "in_ote": ict_ote.get("in_ote_bullish", False) or ict_ote.get("in_ote_bearish", False)
            },
            created_at=now_utc
        )


signal_engine = SignalEngine()
