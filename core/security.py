import time
import re
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from core import get_logger

logger = get_logger("api")


class RateLimiter:
    """
    In-memory rate limiter tracking requests per IP address.
    """

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.client_records: Dict[str, list] = {}

    def is_rate_limited(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - 60.0

        if client_ip not in self.client_records:
            self.client_records[client_ip] = [now]
            return False

        timestamps = [t for t in self.client_records[client_ip] if t > window_start]
        timestamps.append(now)
        self.client_records[client_ip] = timestamps

        if len(timestamps) > self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} ({len(timestamps)} requests/min)")
            return True

        return False


class SettingsUpdateRequest(BaseModel):
    risk_percent: float = Field(ge=0.1, le=10.0, description="Risk percent per trade (0.1% to 10%)")
    default_lot: float = Field(ge=0.01, le=50.0, description="Default fixed lot size")
    max_open_trades: int = Field(ge=1, le=50, description="Maximum simultaneous open trades")
    paper_trading: bool = Field(description="Enable paper trading / simulation mode")

    @field_validator("risk_percent", "default_lot")
    @classmethod
    def validate_positive_values(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Value must be positive")
        return round(v, 2)


class TradeOrderRequest(BaseModel):
    symbol: str = Field(min_length=2, max_length=20, description="Trading symbol (e.g. EURUSD)")
    order_type: str = Field(description="BUY, SELL, BUY_LIMIT, SELL_LIMIT, BUY_STOP, SELL_STOP")
    volume: float = Field(ge=0.01, le=100.0, description="Order volume in lots")
    price: float = Field(default=0.0, ge=0.0, description="Order price for limit/stop orders")
    stop_loss: float = Field(default=0.0, ge=0.0, description="Stop Loss price")
    take_profit: float = Field(default=0.0, ge=0.0, description="Take Profit price")

    @field_validator("symbol")
    @classmethod
    def sanitize_symbol(cls, v: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9._-]", "", v).upper()
        if not clean:
            raise ValueError("Invalid symbol name")
        return clean

    @field_validator("order_type")
    @classmethod
    def validate_order_type(cls, v: str) -> str:
        valid_types = {"BUY", "SELL", "BUY_LIMIT", "SELL_LIMIT", "BUY_STOP", "SELL_STOP"}
        upper_v = v.upper()
        if upper_v not in valid_types:
            raise ValueError(f"Order type must be one of {valid_types}")
        return upper_v


rate_limiter = RateLimiter(requests_per_minute=120)
