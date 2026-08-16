import pytest
import pandas as pd
import numpy as np
from signals import signal_engine, SignalOutput
from strategy import composite_ai_strategy


@pytest.fixture
def signal_sample_df():
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2025-01-01", periods=n, freq="1h")

    # Generate a strong upward trend dataframe
    p = 1.0800 + np.cumsum(np.random.uniform(0.0001, 0.0008, n))

    df = pd.DataFrame({
        "time": dates.astype(int) // 10**9,
        "open": p - 0.0001,
        "high": p + 0.0005,
        "low": p - 0.0002,
        "close": p,
        "tick_volume": np.random.randint(100, 1000, n)
    }, index=dates)
    return df


def test_signal_engine_generation(signal_sample_df):
    sig = signal_engine.generate_signal("EURUSD", signal_sample_df, "H1")
    assert isinstance(sig, SignalOutput)
    assert sig.symbol == "EURUSD"
    assert sig.signal_type in ("BUY", "SELL", "NO_TRADE")
    assert sig.scores.confidence_score >= 0
    assert sig.entry_price > 0


def test_composite_strategy_execution(signal_sample_df):
    sig = composite_ai_strategy.analyze("EURUSD", signal_sample_df)
    assert isinstance(sig, SignalOutput)
    assert sig.scores.confidence_score >= 0
    if sig.signal_type != "NO_TRADE":
        assert sig.stop_loss is not None
        assert sig.take_profit is not None
        assert sig.risk_reward_ratio > 0
