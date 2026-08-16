import pytest
import pandas as pd
import numpy as np
from smc import smc_detector


@pytest.fixture
def smc_sample_df():
    np.random.seed(100)
    n = 100
    dates = pd.date_range("2025-01-01", periods=n, freq="1h")

    # Generate price with a clear bullish trend then retracement
    t = np.linspace(0, 10, n)
    base = 100.0 + np.sin(t) * 5 + t * 0.5

    open_p = base
    high_p = base + np.random.uniform(0.5, 2.0, n)
    low_p = base - np.random.uniform(0.5, 2.0, n)
    close_p = base + np.random.uniform(-1.0, 1.0, n)

    df = pd.DataFrame({
        "time": dates.astype(int) // 10**9,
        "open": open_p,
        "high": high_p,
        "low": low_p,
        "close": close_p,
        "tick_volume": np.random.randint(100, 1000, n)
    }, index=dates)

    # Force a Fair Value Gap
    df.iloc[50, df.columns.get_loc("high")] = 102.0
    df.iloc[51, df.columns.get_loc("open")] = 102.5
    df.iloc[51, df.columns.get_loc("close")] = 105.0
    df.iloc[52, df.columns.get_loc("low")] = 103.5

    return df


def test_smc_detector_fvg(smc_sample_df):
    fvgs = smc_detector.detect_fvg(smc_sample_df)
    assert isinstance(fvgs, list)


def test_smc_detector_order_blocks(smc_sample_df):
    obs = smc_detector.detect_order_blocks(smc_sample_df)
    assert isinstance(obs, list)


def test_smc_detector_structure_and_zones(smc_sample_df):
    struct = smc_detector.detect_structure_and_choch(smc_sample_df)
    assert "bos_bullish" in struct
    assert "choch_bullish" in struct

    zone = smc_detector.get_premium_discount_zone(smc_sample_df)
    assert zone["zone"] in ("PREMIUM", "DISCOUNT", "EQUILIBRIUM")
    assert 0 <= zone["fib_level_percent"] <= 100


def test_smc_complete_analysis(smc_sample_df):
    result = smc_detector.analyze(smc_sample_df)
    assert "fair_value_gaps" in result
    assert "order_blocks" in result
    assert "structure" in result
    assert "pricing_zone" in result
