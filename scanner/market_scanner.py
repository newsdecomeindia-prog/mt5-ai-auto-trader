import enum
from typing import List, Dict, Any, Optional
from market import market_data_provider
from mt5 import mt5_client
from core import get_logger

logger = get_logger("trading")


class MarketCategory(str, enum.Enum):
    FOREX = "Forex"
    GOLD = "Gold"
    SILVER = "Silver"
    CRYPTO = "Crypto"
    INDICES = "Indices"
    CFDS = "CFDs"
    UNKNOWN = "Unknown"


class MarketScanner:
    """
    Multi-asset market watch scanner.
    Categorizes symbols and scans liquidity, spreads, and market activity.
    """

    DEFAULT_SYMBOLS = {
        MarketCategory.FOREX: ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "EURGBP"],
        MarketCategory.GOLD: ["XAUUSD"],
        MarketCategory.SILVER: ["XAGUSD"],
        MarketCategory.CRYPTO: ["BTCUSD", "ETHUSD"],
        MarketCategory.INDICES: ["US30", "US500", "NAS100", "GER40"],
        MarketCategory.CFDS: ["OIL", "BRENT", "UK100"]
    }

    def categorize_symbol(self, symbol: str) -> MarketCategory:
        sym_upper = symbol.upper()
        if "XAU" in sym_upper or "GOLD" in sym_upper:
            return MarketCategory.GOLD
        if "XAG" in sym_upper or "SILVER" in sym_upper:
            return MarketCategory.SILVER
        if any(c in sym_upper for c in ["BTC", "ETH", "SOL", "XRP", "CRYPTO"]):
            return MarketCategory.CRYPTO
        if any(idx in sym_upper for idx in ["US30", "US500", "NAS100", "GER40", "SPX", "NDX", "DJI"]):
            return MarketCategory.INDICES
        if any(cfd in sym_upper for cfd in ["OIL", "BRENT", "GAS", "WTI"]):
            return MarketCategory.CFDS
        if len(sym_upper) == 6 and (sym_upper[:3].isalpha() and sym_upper[3:].isalpha()):
            return MarketCategory.FOREX
        return MarketCategory.UNKNOWN

    def scan_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Scans individual symbol for current price, spread, ATR, and tradability."""
        tick = market_data_provider.get_tick(symbol)
        sym_info = market_data_provider.get_symbol_info(symbol)
        if not tick or not sym_info:
            return None

        spread_pips = market_data_provider.get_spread(symbol)
        df = market_data_provider.get_ohlc(symbol, timeframe="H1", count=50)
        atr = market_data_provider.calculate_atr(df, period=14) if not df.empty else 0.0

        category = self.categorize_symbol(symbol)

        return {
            "symbol": symbol,
            "category": category.value,
            "bid": tick.bid,
            "ask": tick.ask,
            "spread_pips": spread_pips,
            "atr_h1": round(atr, sym_info.digits),
            "digits": sym_info.digits,
            "tradable": sym_info.visible and spread_pips < 50
        }

    def scan_all(self, target_categories: Optional[List[MarketCategory]] = None) -> List[Dict[str, Any]]:
        """Scans all configured watch symbols across requested market categories."""
        symbols_to_scan = []
        if target_categories:
            for cat in target_categories:
                symbols_to_scan.extend(self.DEFAULT_SYMBOLS.get(cat, []))
        else:
            for category_symbols in self.DEFAULT_SYMBOLS.values():
                symbols_to_scan.extend(category_symbols)

        # Sync Market Watch
        mt5_client.sync_market_watch(symbols_to_scan)

        results = []
        for sym in symbols_to_scan:
            scan_res = self.scan_symbol(sym)
            if scan_res:
                results.append(scan_res)

        logger.info(f"Market scanner completed scan for {len(results)} symbols.")
        return results


market_scanner = MarketScanner()
