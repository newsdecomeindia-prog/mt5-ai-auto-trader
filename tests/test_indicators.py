import pytest
import pandas as pd
import numpy as np
from indicators import technical_indicators
from strategy.price_action import price_action_detector


@pytest.fixture
def sample_df():
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2025-01-01", periods=n, freq="1h")
    price = 1.0800 + np.cumsum(np.random.normal(0, 0.001, n))
    high = price + abs(np.random.normal(0, 0.0005, n))
    low = price - abs(np.random.normal(0, 0.0005, n))
    open_p = price + np.random.normal(0, 0.0002, n)
    close = price

    df = pd.DataFrame({
        "time": dates.astype(int) // 10**9,
        "open": open_p,
        "high": high,
        "low": low,
        "close": close,
        "tick_volume": np.random.randint(100, 1000, n)
    }, index=dates)
    return df


def test_all_technical_indicators(sample_df):
    close = sample_df["close"]

    # SMA & EMA
    sma = technical_indicators.sma(close, 14)
    ema = technical_indicators.ema(close, 14)
    assert not sma.isna().all()
    assert not ema.isna().all()

    # RSI
    rsi = technical_indicators.rsi(close, 14)
    assert 0 <= rsi.iloc[-1] <= 100

    # MACD
    macd, signal, hist = technical_indicators.macd(close)
    assert len(macd) == len(close)

    # ATR & ADX
    atr = technical_indicators.atr(sample_df, 14)
    adx = technical_indicators.adx(sample_df, 14)
    assert atr.iloc[-1] > 0
    assert adx.iloc[-1] >= 0

    # VWAP & CCI
    vwap = technical_indicators.vwap(sample_df)
    cci = technical_indicators.cci(sample_df)
    assert vwap.iloc[-1] > 0

    # Stochastic & Momentum
    k, d = technical_indicators.stochastic(sample_df)
    mom = technical_indicators.momentum(close, 14)
    assert 0 <= k.iloc[-1] <= 100

    # SuperTrend
    st, direction = technical_indicators.supertrend(sample_df)
    assert direction.iloc[-1] in (1, -1)

    # Bollinger Bands
    upper, mid, lower = technical_indicators.bollinger_bands(close)
    assert upper.iloc[-1] >= mid.iloc[-1] >= lower.iloc[-1]

    # Ichimoku & Donchian
    ich = technical_indicators.ichimoku(sample_df)
    d_up, d_mid, d_low = technical_indicators.donchian_channel(sample_df)
    assert "tenkan_sen" in ich
    assert d_up.iloc[-1] >= d_low.iloc[-1]


def test_price_action_patterns(sample_df):
    patterns = price_action_detector.detect_patterns(sample_df)
    assert isinstance(patterns, dict)
    assert "pin_bar_bullish" in patterns
    assert "engulfing_bullish" in patterns
    assert "inside_bar" in patterns
    assert "breakout_bullish" in patterns
