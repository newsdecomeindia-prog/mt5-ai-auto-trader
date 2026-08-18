from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from database.models import (
    Trade, Order, Signal, SystemLog, Setting, Statistic, PerformanceRecord,
    TradeStatus, OrderStatus, utc_now
)


class TradeRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> Trade:
        trade = Trade(**kwargs)
        self.session.add(trade)
        self.session.flush()
        return trade

    def get_by_ticket(self, ticket: int) -> Optional[Trade]:
        return self.session.query(Trade).filter(Trade.ticket == ticket).first()

    def get_open_trades(self, symbol: Optional[str] = None) -> List[Trade]:
        query = self.session.query(Trade).filter(Trade.status == TradeStatus.OPEN.value)
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        return query.all()

    def update_trade(self, ticket: int, **kwargs) -> Optional[Trade]:
        trade = self.get_by_ticket(ticket)
        if trade:
            for key, value in kwargs.items():
                if hasattr(trade, key):
                    setattr(trade, key, value)
            self.session.flush()
        return trade

    def close_trade(self, ticket: int, close_price: float, profit: float, exit_reason: str = "CLOSED") -> Optional[Trade]:
        return self.update_trade(
            ticket,
            close_price=close_price,
            profit=profit,
            status=TradeStatus.CLOSED.value,
            close_time=utc_now(),
            exit_reason=exit_reason
        )

    def get_trade_history(self, limit: int = 100) -> List[Trade]:
        return self.session.query(Trade).order_by(Trade.open_time.desc()).limit(limit).all()


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> Order:
        order = Order(**kwargs)
        self.session.add(order)
        self.session.flush()
        return order

    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self.session.query(Order).filter(Order.order_id == order_id).first()

    def get_pending_orders(self, symbol: Optional[str] = None) -> List[Order]:
        query = self.session.query(Order).filter(Order.status == OrderStatus.PENDING.value)
        if symbol:
            query = query.filter(Order.symbol == symbol)
        return query.all()

    def update_status(self, order_id: int, status: str) -> Optional[Order]:
        order = self.get_by_id(order_id)
        if order:
            order.status = status
            order.updated_at = utc_now()
            self.session.flush()
        return order


class SignalRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> Signal:
        signal = Signal(**kwargs)
        self.session.add(signal)
        self.session.flush()
        return signal

    def get_latest(self, symbol: Optional[str] = None, limit: int = 50) -> List[Signal]:
        query = self.session.query(Signal)
        if symbol:
            query = query.filter(Signal.symbol == symbol)
        return query.order_by(Signal.created_at.desc()).limit(limit).all()


class LogRepository:
    def __init__(self, session: Session):
        self.session = session

    def log(self, category: str, message: str, level: str = "INFO", details: Optional[str] = None) -> SystemLog:
        log_entry = SystemLog(
            category=category,
            level=level,
            message=message,
            details=details,
            created_at=utc_now()
        )
        self.session.add(log_entry)
        self.session.flush()
        return log_entry

    def get_logs(self, category: Optional[str] = None, limit: int = 100) -> List[SystemLog]:
        query = self.session.query(SystemLog)
        if category:
            query = query.filter(SystemLog.category == category)
        return query.order_by(SystemLog.created_at.desc()).limit(limit).all()


class SettingRepository:
    def __init__(self, session: Session):
        self.session = session

    def set(self, key: str, value: str, description: Optional[str] = None) -> Setting:
        setting = self.session.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = str(value)
            if description:
                setting.description = description
            setting.updated_at = utc_now()
        else:
            setting = Setting(key=key, value=str(value), description=description)
            self.session.add(setting)
        self.session.flush()
        return setting

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        setting = self.session.query(Setting).filter(Setting.key == key).first()
        return setting.value if setting else default

    def get_all(self) -> Dict[str, str]:
        settings_records = self.session.query(Setting).all()
        return {s.key: s.value for s in settings_records}


class StatisticsRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_stats(self, **kwargs) -> Statistic:
        stat = Statistic(**kwargs)
        self.session.add(stat)
        self.session.flush()
        return stat

    def get_latest(self) -> Optional[Statistic]:
        return self.session.query(Statistic).order_by(Statistic.date.desc()).first()


class PerformanceRepository:
    def __init__(self, session: Session):
        self.session = session

    def record_snapshot(self, balance: float, equity: float, margin: float = 0.0,
                        free_margin: float = 0.0, open_pnl: float = 0.0,
                        drawdown_percent: float = 0.0) -> PerformanceRecord:
        record = PerformanceRecord(
            balance=balance,
            equity=equity,
            margin=margin,
            free_margin=free_margin,
            open_pnl=open_pnl,
            drawdown_percent=drawdown_percent,
            timestamp=utc_now()
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_history(self, limit: int = 100) -> List[PerformanceRecord]:
        return self.session.query(PerformanceRecord).order_by(PerformanceRecord.timestamp.asc()).limit(limit).all()
