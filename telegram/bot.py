import httpx
import asyncio
from typing import Dict, Any, Optional
from config import settings
from core import get_logger

logger = get_logger("general")


class TelegramNotifier:
    """
    Telegram Notification Bot & Interactive Alert System.
    Sends trade open, trade close, SL hit, TP hit, error, daily/weekly summary notifications.
    """

    def __init__(self, token: str = settings.TELEGRAM_TOKEN, chat_id: str = settings.TELEGRAM_CHAT_ID):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage" if self.token else ""

    async def send_message(self, text: str) -> bool:
        """Async sends Markdown message to Telegram chat."""
        if not self.token or not self.chat_id:
            logger.info(f"[TELEGRAM MOCK ALERT]\n{text}")
            return True

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    self.api_url,
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "Markdown"
                    }
                )
                if resp.status_code == 200:
                    return True
                else:
                    logger.error(f"Telegram API response error: {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def _schedule_message(self, text: str) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.send_message(text))
        except RuntimeError:
            logger.info(f"[TELEGRAM MOCK ALERT]\n{text}")

    def notify_trade_open(self, symbol: str, order_type: str, volume: float, price: float, sl: Optional[float], tp: Optional[float], ticket: int) -> None:
        text = (
            f"🚀 *TRADE OPENED*\n\n"
            f"• *Ticket:* `{ticket}`\n"
            f"• *Symbol:* `{symbol}`\n"
            f"• *Type:* `{order_type}`\n"
            f"• *Volume:* `{volume} lots`\n"
            f"• *Open Price:* `{price:.5f}`\n"
            f"• *Stop Loss:* `{sl if sl else 'None'}`\n"
            f"• *Take Profit:* `{tp if tp else 'None'}`"
        )
        self._schedule_message(text)

    def notify_trade_close(self, ticket: int, symbol: str, close_price: float, profit: float, reason: str) -> None:
        emoji = "✅" if profit >= 0 else "❌"
        text = (
            f"{emoji} *TRADE CLOSED*\n\n"
            f"• *Ticket:* `{ticket}`\n"
            f"• *Symbol:* `{symbol}`\n"
            f"• *Close Price:* `{close_price:.5f}`\n"
            f"• *Profit:* `${profit:+.2f}`\n"
            f"• *Exit Reason:* `{reason}`"
        )
        self._schedule_message(text)

    def notify_error(self, category: str, error_message: str) -> None:
        text = (
            f"⚠️ *SYSTEM ERROR ALERT*\n\n"
            f"• *Category:* `{category}`\n"
            f"• *Error:* `{error_message}`"
        )
        self._schedule_message(text)

    def notify_summary(self, summary_type: str, metrics: Dict[str, Any]) -> None:
        text = (
            f"📊 *{summary_type.upper()} PERFORMANCE SUMMARY*\n\n"
            f"• *Total Trades:* `{metrics.get('total_trades', 0)}`\n"
            f"• *Win Rate:* `{metrics.get('win_rate', 0)}%`\n"
            f"• *Total Profit:* `${metrics.get('total_profit', 0):+.2f}`\n"
            f"• *Profit Factor:* `{metrics.get('profit_factor', 0)}`\n"
            f"• *Max Drawdown:* `{metrics.get('max_drawdown', 0)}%`"
        )
        self._schedule_message(text)


telegram_notifier = TelegramNotifier()
