import pytest
import pandas as pd
from market import market_data_provider, Timeframe
from scanner import market_scanner, MarketCategory


def test_timeframe_mapping():
    assert Timeframe.M1.value == "M1"
    assert Timeframe.H1.value == "H1"
    assert Timeframe.D1.value == "D1"


def test_market_data_provider_ohlc_and_atr():
    df = market_data_provider.get_ohlc("EURUSD", "H1", 50)
    assert not df.empty
    assert "close" in df.columns
    assert "high" in df.columns
    assert "low" in df.columns

    atr = market_data_provider.calculate_atr(df, period=14)
    assert atr > 0


def test_market_scanner_categorization():
    assert market_scanner.categorize_symbol("EURUSD") == MarketCategory.FOREX
    assert market_scanner.categorize_symbol("XAUUSD") == MarketCategory.GOLD
    assert market_scanner.categorize_symbol("XAGUSD") == MarketCategory.SILVER
    assert market_scanner.categorize_symbol("BTCUSD") == MarketCategory.CRYPTO
    assert market_scanner.categorize_symbol("US30") == MarketCategory.INDICES


def test_market_scanner_scan_all():
    results = market_scanner.scan_all([MarketCategory.FOREX, MarketCategory.GOLD])
    assert len(results) > 0
    symbols = [r["symbol"] for r in results]
    assert "EURUSD" in symbols
    assert "XAUUSD" in symbols
