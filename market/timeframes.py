import enum
from typing import Dict, Any

try:
    import MetaTrader5 as mt5
    TIMEFRAME_MAP: Dict[str, Any] = {
        "M1": getattr(mt5, "TIMEFRAME_M1", 1),
        "M5": getattr(mt5, "TIMEFRAME_M5", 5),
        "M15": getattr(mt5, "TIMEFRAME_M15", 15),
        "M30": getattr(mt5, "TIMEFRAME_M30", 30),
        "H1": getattr(mt5, "TIMEFRAME_H1", 16385),
        "H4": getattr(mt5, "TIMEFRAME_H4", 16388),
        "D1": getattr(mt5, "TIMEFRAME_D1", 16408),
        "W1": getattr(mt5, "TIMEFRAME_W1", 32769),
        "MN1": getattr(mt5, "TIMEFRAME_MN1", 49153),
    }
except ImportError:
    TIMEFRAME_MAP = {
        "M1": 1,
        "M5": 5,
        "M15": 15,
        "M30": 30,
        "H1": 60,
        "H4": 240,
        "D1": 1440,
        "W1": 10080,
        "MN1": 43200,
    }


class Timeframe(str, enum.Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"

    @property
    def mt5_val(self):
        return TIMEFRAME_MAP.get(self.value, 1)
