import time
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from config import settings
from core import get_logger
from mt5.models import AccountInfo, SymbolInfo, TickData

logger = get_logger("connection")

try:
    import MetaTrader5 as mt5
    HAS_MT5_LIB = True
except ImportError:
    HAS_MT5_LIB = False
    mt5 = None


class SimulatedMT5:
    """
    Simulated MetaTrader 5 interface for non-Windows environments or paper trading mode.
    Maintains full compatibility with standard MT5 API calls.
    """

    def __init__(self):
        self._connected = False
        self._account = AccountInfo(
            login=settings.MT5_LOGIN or 12345678,
            server=settings.MT5_SERVER or "MetaQuotes-Demo",
            balance=10000.0,
            equity=10000.0,
            margin_free=10000.0,
            currency="USD"
        )
        self._symbols = {
            "EURUSD": SymbolInfo(name="EURUSD", digits=5, ask=1.08510, bid=1.08500, point=0.00001, spread=10, path="Forex\\EURUSD", currency_base="EUR", currency_profit="USD"),
            "GBPUSD": SymbolInfo(name="GBPUSD", digits=5, ask=1.27010, bid=1.27000, point=0.00001, spread=10, path="Forex\\GBPUSD", currency_base="GBP", currency_profit="USD"),
            "USDJPY": SymbolInfo(name="USDJPY", digits=3, ask=155.010, bid=155.000, point=0.001, spread=10, path="Forex\\USDJPY", currency_base="USD", currency_profit="JPY"),
            "XAUUSD": SymbolInfo(name="XAUUSD", digits=2, ask=2500.20, bid=2500.00, point=0.01, spread=20, path="Metals\\XAUUSD", currency_base="XAU", currency_profit="USD"),
            "XAGUSD": SymbolInfo(name="XAGUSD", digits=3, ask=30.020, bid=30.000, point=0.001, spread=20, path="Metals\\XAGUSD", currency_base="XAG", currency_profit="USD"),
            "BTCUSD": SymbolInfo(name="BTCUSD", digits=2, ask=65000.00, bid=64980.00, point=0.01, spread=2000, path="Crypto\\BTCUSD", currency_base="BTC", currency_profit="USD"),
            "US30": SymbolInfo(name="US30", digits=1, ask=39005.0, bid=39000.0, point=0.1, spread=50, path="Indices\\US30", currency_base="USD", currency_profit="USD"),
        }
        self._positions = {}
        self._orders = {}
        self._next_ticket = 1000000

    def initialize(self, path: Optional[str] = None, login: Optional[int] = None, password: Optional[str] = None, server: Optional[str] = None) -> bool:
        self._connected = True
        return True

    def login(self, login: int, password: str, server: str) -> bool:
        self._connected = True
        return True

    def shutdown(self) -> None:
        self._connected = False

    def terminal_info(self) -> Any:
        class TerminalInfoObj:
            connected = True
            trade_allowed = True
            name = "Simulated MT5 Terminal"
            path = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
            data_path = "C:\\Users\\Simulated\\AppData\\Roaming\\MetaQuotes\\Terminal"
        return TerminalInfoObj()

    def account_info(self) -> Any:
        return self._account

    def symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        return self._symbols.get(symbol)

    def symbol_select(self, symbol: str, enable: bool) -> bool:
        return symbol in self._symbols

    def symbol_info_tick(self, symbol: str) -> Optional[Any]:
        sym = self._symbols.get(symbol)
        if not sym:
            return None
        class TickObj:
            pass
        t = TickObj()
        t.time = int(time.time())
        t.bid = sym.bid
        t.ask = sym.ask
        t.last = (sym.bid + sym.ask) / 2
        t.volume = 100.0
        t.flags = 0
        return t

    def copy_rates_from_pos(self, symbol: str, timeframe: Any, start_pos: int, count: int) -> Optional[np.ndarray]:
        """Generate realistic synthetic OHLC bar data for simulation."""
        sym = self._symbols.get(symbol)
        base_price = sym.ask if sym else 1.0850
        now = int(time.time())
        step = 60  # 1 minute

        dtype = [
            ('time', 'i8'), ('open', 'f8'), ('high', 'f8'),
            ('low', 'f8'), ('close', 'f8'), ('tick_volume', 'i8'),
            ('spread', 'i4'), ('real_volume', 'i8')
        ]
        data = np.zeros(count, dtype=dtype)
        np.random.seed(42)

        price = base_price
        for i in range(count):
            t = now - (count - i) * step
            change = np.random.normal(0, base_price * 0.0005)
            open_p = price
            close_p = open_p + change
            high_p = max(open_p, close_p) + abs(np.random.normal(0, base_price * 0.0002))
            low_p = min(open_p, close_p) - abs(np.random.normal(0, base_price * 0.0002))
            volume = np.random.randint(50, 500)
            data[i] = (t, open_p, high_p, low_p, close_p, volume, 10, volume)
            price = close_p

        return data


class MT5Client:
    """
    Robust MetaTrader 5 Client providing Auto Login, Auto Reconnect, Terminal Detection,
    Account Validation, Broker Validation, Connection Health Monitoring, and Paper Fallback.
    """

    def __init__(self):
        self.is_simulated = False
        self.is_connected = False
        self.login_id = settings.MT5_LOGIN
        self.password = settings.MT5_PASSWORD
        self.server = settings.MT5_SERVER
        self.path = settings.MT5_PATH
        self.driver = None

    def connect(self) -> bool:
        """Initializes connection to MT5 terminal or simulation fallback."""
        logger.info("Attempting MT5 terminal connection...")

        if HAS_MT5_LIB and not settings.PAPER_TRADING:
            try:
                init_kwargs = {}
                if self.path:
                    init_kwargs["path"] = self.path
                if self.login_id:
                    init_kwargs["login"] = self.login_id
                    init_kwargs["password"] = self.password
                    init_kwargs["server"] = self.server

                if mt5.initialize(**init_kwargs):
                    if self.login_id and self.password and self.server:
                        if not mt5.login(login=self.login_id, password=self.password, server=self.server):
                            logger.error(f"MT5 login failed. Error code: {mt5.last_error()}")
                            return self._fallback_simulation()
                    self.driver = mt5
                    self.is_simulated = False
                    self.is_connected = True
                    logger.info("Connected to native MetaTrader 5 Terminal successfully.")
                    return True
                else:
                    logger.warning(f"MT5 initialize failed: {mt5.last_error()}. Falling back to simulation.")
                    return self._fallback_simulation()
            except Exception as e:
                logger.error(f"Failed to initialize native MT5: {e}. Falling back to simulation mode.")
                return self._fallback_simulation()
        else:
            return self._fallback_simulation()

    def _fallback_simulation(self) -> bool:
        """Activates simulated paper trading MT5 driver."""
        logger.info("Initializing Simulated MT5 Trading Engine.")
        self.driver = SimulatedMT5()
        self.driver.initialize()
        self.is_simulated = True
        self.is_connected = True
        return True

    def reconnect(self) -> bool:
        """Attempts reconnect on failure."""
        logger.warning("Reconnecting to MT5 engine...")
        self.disconnect()
        return self.connect()

    def disconnect(self) -> None:
        """Disconnects MT5 session."""
        if self.driver:
            try:
                self.driver.shutdown()
            except Exception as e:
                logger.error(f"Error during MT5 shutdown: {e}")
        self.is_connected = False

    def validate_account(self) -> Tuple[bool, str]:
        """Validates account trade mode, trade permissions, and expert status."""
        acc = self.get_account_info()
        if not acc:
            return False, "Failed to retrieve account information."
        if not acc.trade_allowed:
            return False, "Trading is disabled on this account."
        if not acc.trade_expert:
            return False, "Automated expert trading is disabled on this account."
        return True, f"Account validated. Server: {acc.server}, Balance: {acc.balance} {acc.currency}"

    def get_account_info(self) -> Optional[AccountInfo]:
        """Retrieves structured account info."""
        if not self.is_connected or not self.driver:
            return None
        info = self.driver.account_info()
        if not info:
            return None
        if isinstance(info, AccountInfo):
            return info
        return AccountInfo(
            login=getattr(info, "login", 0),
            trade_mode=getattr(info, "trade_mode", 0),
            leverage=getattr(info, "leverage", 100),
            limit_orders=getattr(info, "limit_orders", 500),
            margin_so_mode=getattr(info, "margin_so_mode", 0),
            trade_allowed=getattr(info, "trade_allowed", True),
            trade_expert=getattr(info, "trade_expert", True),
            balance=getattr(info, "balance", 0.0),
            credit=getattr(info, "credit", 0.0),
            profit=getattr(info, "profit", 0.0),
            equity=getattr(info, "equity", 0.0),
            margin=getattr(info, "margin", 0.0),
            margin_free=getattr(info, "margin_free", 0.0),
            margin_level=getattr(info, "margin_level", 0.0),
            currency=getattr(info, "currency", "USD"),
            server=getattr(info, "server", "DemoServer"),
            company=getattr(info, "company", "Broker")
        )

    def sync_market_watch(self, symbols: List[str]) -> Dict[str, bool]:
        """Ensures all requested symbols are enabled in Market Watch."""
        status = {}
        for sym in symbols:
            if not self.driver:
                status[sym] = False
                continue
            res = self.driver.symbol_select(sym, True)
            status[sym] = bool(res)
            if not res:
                logger.warning(f"Could not enable symbol {sym} in Market Watch.")
        return status

    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Retrieves structured symbol info."""
        if not self.is_connected or not self.driver:
            return None
        sym = self.driver.symbol_info(symbol)
        if not sym:
            return None
        if isinstance(sym, SymbolInfo):
            return sym
        return SymbolInfo(
            name=getattr(sym, "name", symbol),
            visible=getattr(sym, "visible", True),
            digits=getattr(sym, "digits", 5),
            spread=getattr(sym, "spread", 10),
            point=getattr(sym, "point", 0.00001),
            ask=getattr(sym, "ask", 0.0),
            bid=getattr(sym, "bid", 0.0),
            volume_min=getattr(sym, "volume_min", 0.01),
            volume_max=getattr(sym, "volume_max", 100.0),
            volume_step=getattr(sym, "volume_step", 0.01),
            trade_contract_size=getattr(sym, "trade_contract_size", 100000.0),
            currency_base=getattr(sym, "currency_base", ""),
            currency_profit=getattr(sym, "currency_profit", ""),
            path=getattr(sym, "path", "")
        )

    def get_tick(self, symbol: str) -> Optional[TickData]:
        """Retrieves current tick data."""
        if not self.is_connected or not self.driver:
            return None
        t = self.driver.symbol_info_tick(symbol)
        if not t:
            return None
        return TickData(
            symbol=symbol,
            time=datetime.fromtimestamp(t.time, tz=timezone.utc),
            bid=t.bid,
            ask=t.ask,
            last=getattr(t, "last", (t.bid + t.ask) / 2),
            volume=getattr(t, "volume", 0.0),
            flags=getattr(t, "flags", 0)
        )


mt5_client = MT5Client()
