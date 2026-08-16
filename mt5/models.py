from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class AccountInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    login: int
    trade_mode: int = 0  # 0: demo, 1: contest, 2: real
    leverage: int = 100
    limit_orders: int = 500
    margin_so_mode: int = 0
    trade_allowed: bool = True
    trade_expert: bool = True
    balance: float = 10000.0
    credit: float = 0.0
    profit: float = 0.0
    equity: float = 10000.0
    margin: float = 0.0
    margin_free: float = 10000.0
    margin_level: float = 0.0
    margin_so_call: float = 50.0
    margin_so_so: float = 30.0
    currency: str = "USD"
    server: str = "MetaQuotes-Demo"
    company: str = "MetaQuotes Software Corp."


class SymbolInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    visible: bool = True
    digits: int = 5
    spread: int = 10
    point: float = 0.00001
    ask: float = 1.08510
    bid: float = 1.08500
    volume_min: float = 0.01
    volume_max: float = 100.0
    volume_step: float = 0.01
    trade_contract_size: float = 100000.0
    currency_base: str = "EUR"
    currency_profit: str = "USD"
    path: str = "Forex\\EURUSD"


class TickData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    time: datetime
    bid: float
    ask: float
    last: float
    volume: float
    flags: int = 0
