import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from ict import ict_detector


@pytest.fixture
def ict_sample_df():
    np.random.seed(42)
    n = 60
    dates = pd.date_range("2025-01-01", periods=n, freq="1h")
    price = 1.0800 + np.cumsum(np.random.normal(0, 0.001, n))

    df = pd.DataFrame({
        "time": dates.astype(int) // 10**9,
        "open": price,
        "high": price + 0.0010,
        "low": price - 0.0010,
        "close": price + 0.0002,
        "tick_volume": np.random.randint(100, 500, n)
    }, index=dates)
    return df


def test_ict_kill_zones():
    kz = ict_detector.get_current_kill_zone(datetime(2025, 1, 1, 8, 30, tzinfo=timezone.utc))
    assert kz["active_zone"] == "LONDON"
    assert kz["is_kill_zone_active"] is True


def test_ict_ote_calculation(ict_sample_df):
    ote = ict_detector.calculate_ote(ict_sample_df)
    assert "fib_618" in ote
    assert "fib_705" in ote
    assert "fib_790" in ote
    assert ote["swing_high"] >= ote["swing_low"]


def test_ict_liquidity_pools_and_amd(ict_sample_df):
    pools = ict_detector.detect_liquidity_pools(ict_sample_df)
    assert pools["buy_side_liquidity"] >= pools["sell_side_liquidity"]

    amd = ict_detector.detect_power_of_three(ict_sample_df)
    assert amd["phase"] in ("ACCUMULATION", "MANIPULATION", "DISTRIBUTION")


def test_ict_daily_bias_and_full_analysis(ict_sample_df):
    bias = ict_detector.determine_daily_bias(ict_sample_df)
    assert bias["bias"] in ("BULLISH", "BEARISH", "NEUTRAL")

    full = ict_detector.analyze(ict_sample_df, ict_sample_df)
    assert "kill_zone" in full
    assert "ote" in full
    assert "liquidity_pools" in full
    assert "daily_bias" in full
