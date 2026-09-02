import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from pydantic import BaseModel
from database import get_db, db_manager, TradeRepository, SettingRepository, StatisticsRepository, PerformanceRepository, TradeStatus
from core.security import SettingsUpdateRequest, TradeOrderRequest, rate_limiter
from mt5 import mt5_client, health_monitor
from execution import execution_engine, trade_manager
from analytics import performance_analytics
from core import get_logger

logger = get_logger("api")
api_router = APIRouter()

SYSTEM_STATE = {
    "is_running": True,
    "started_at": None
}


class ConnectionManager:
    """Manages active WebSocket client connections for real-time live streaming."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket client disconnected.")

    async def broadcast(self, data: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting WebSocket message: {e}")
                self.disconnect(connection)


ws_manager = ConnectionManager()


@api_router.get("/health", summary="Health Check")
async def health_check():
    """Returns platform and MT5 connection health status."""
    return health_monitor.check_health()


@api_router.get("/status", summary="System Status")
async def get_status():
    """Returns platform operational status and active MT5 account info."""
    acc = mt5_client.get_account_info()
    return {
        "is_running": SYSTEM_STATE["is_running"],
        "is_simulated": mt5_client.is_simulated,
        "is_connected": mt5_client.is_connected,
        "account": acc.model_dump() if acc else None
    }


@api_router.post("/start", summary="Start Auto Trading Engine")
async def start_engine():
    SYSTEM_STATE["is_running"] = True
    logger.info("Auto trading engine started via API.")
    return {"message": "Auto trading engine started.", "status": "running"}


@api_router.post("/stop", summary="Stop Auto Trading Engine")
async def stop_engine():
    SYSTEM_STATE["is_running"] = False
    logger.warning("Auto trading engine stopped via API.")
    return {"message": "Auto trading engine stopped.", "status": "stopped"}


@api_router.post("/restart", summary="Restart MT5 & Trading Engine")
async def restart_engine():
    mt5_client.reconnect()
    SYSTEM_STATE["is_running"] = True
    logger.info("Platform engine restarted via API.")
    return {"message": "Platform engine restarted successfully."}


@api_router.get("/open-trades", summary="Get Open Trades")
async def get_open_trades():
    """Returns currently active open positions."""
    with db_manager.get_session() as session:
        repo = TradeRepository(session)
        trades = repo.get_open_trades()
        return [
            {
                "ticket": t.ticket,
                "symbol": t.symbol,
                "order_type": t.order_type,
                "volume": t.volume,
                "open_price": t.open_price,
                "stop_loss": t.stop_loss,
                "take_profit": t.take_profit,
                "profit": t.profit,
                "status": t.status,
                "open_time": str(t.open_time)
            }
            for t in trades
        ]


@api_router.get("/history", summary="Get Trade History")
async def get_trade_history(limit: int = 100):
    """Returns closed trade history."""
    with db_manager.get_session() as session:
        repo = TradeRepository(session)
        trades = repo.get_trade_history(limit=limit)
        return [
            {
                "ticket": t.ticket,
                "symbol": t.symbol,
                "order_type": t.order_type,
                "volume": t.volume,
                "open_price": t.open_price,
                "close_price": t.close_price,
                "profit": t.profit,
                "status": t.status,
                "exit_reason": t.exit_reason,
                "open_time": str(t.open_time),
                "close_time": str(t.close_time) if t.close_time else None
            }
            for t in trades
        ]


@api_router.get("/statistics", summary="Get Performance Statistics")
async def get_statistics():
    """Returns performance analytics metrics."""
    with db_manager.get_session() as session:
        repo = TradeRepository(session)
        all_trades = repo.get_trade_history(limit=500)
        return performance_analytics.calculate_trade_metrics(all_trades)


@api_router.get("/settings", summary="Get Current Settings")
async def get_settings():
    """Returns application configuration settings."""
    with db_manager.get_session() as session:
        repo = SettingRepository(session)
        return repo.get_all()


@api_router.post("/settings", summary="Update Settings")
async def update_settings(body: SettingsUpdateRequest):
    """Updates system settings."""
    with db_manager.get_session() as session:
        repo = SettingRepository(session)
        repo.set("RISK_PERCENT", str(body.risk_percent))
        repo.set("DEFAULT_LOT", str(body.default_lot))
        repo.set("MAX_OPEN_TRADES", str(body.max_open_trades))
        repo.set("PAPER_TRADING", str(body.paper_trading))
    return {"message": "Settings updated successfully."}


@api_router.post("/order", summary="Execute Order")
async def place_order(order: TradeOrderRequest):
    """Places market or pending order."""
    ok, ticket, msg = execution_engine.execute_order(
        symbol=order.symbol,
        order_type=order.order_type,
        volume=order.volume,
        price=order.price if order.price > 0 else None,
        stop_loss=order.stop_loss if order.stop_loss > 0 else None,
        take_profit=order.take_profit if order.take_profit > 0 else None
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ticket": ticket, "message": msg}


@api_router.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """Real-time WebSocket endpoint pushing live updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            acc = mt5_client.get_account_info()
            data = {
                "timestamp": str(asyncio.get_event_loop().time()),
                "is_running": SYSTEM_STATE["is_running"],
                "balance": acc.balance if acc else 0.0,
                "equity": acc.equity if acc else 0.0,
                "free_margin": acc.margin_free if acc else 0.0,
            }
            await websocket.send_json(data)
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
