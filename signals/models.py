from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class SignalScores(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    confidence_score: float = 0.0  # 0 to 100
    trade_score: float = 0.0       # 0 to 100
    probability_score: float = 0.0 # 0 to 100


class SignalOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    timeframe: str = "H1"
    signal_type: str = "NO_TRADE"  # BUY, SELL, NO_TRADE
    scores: SignalScores
    entry_price: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: float = 0.0
    indicators: Dict[str, Any] = {}
    price_action: Dict[str, Any] = {}
    smc: Dict[str, Any] = {}
    ict: Dict[str, Any] = {}
    created_at: datetime
