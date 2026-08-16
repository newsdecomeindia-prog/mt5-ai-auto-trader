import time
from typing import Dict, Any
from core import get_logger
from mt5.client import mt5_client

logger = get_logger("connection")


class MT5HealthMonitor:
    """
    Monitors MT5 connection status, terminal health, latency, and auto-reconnects on drop.
    """

    def __init__(self, check_interval: int = 10):
        self.check_interval = check_interval
        self.last_check_time = 0.0
        self.consecutive_failures = 0
        self.max_failures = 3

    def check_health(self) -> Dict[str, Any]:
        """Performs health check on MT5 connection."""
        start_time = time.time()
        is_ok = False
        latency_ms = 0.0
        details = ""

        try:
            if not mt5_client.is_connected:
                is_ok = mt5_client.connect()
                details = "Reconnected" if is_ok else "Connection failed"
            else:
                account = mt5_client.get_account_info()
                if account and account.balance >= 0:
                    is_ok = True
                    details = "Health check passed"
                else:
                    is_ok = False
                    details = "Account query returned invalid state"

            latency_ms = round((time.time() - start_time) * 1000, 2)

            if is_ok:
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
                logger.warning(f"MT5 Health Check failed ({self.consecutive_failures}/{self.max_failures}): {details}")
                if self.consecutive_failures >= self.max_failures:
                    logger.error("Max consecutive failures reached. Triggering MT5 reconnect...")
                    mt5_client.reconnect()
                    self.consecutive_failures = 0

        except Exception as e:
            self.consecutive_failures += 1
            details = f"Exception in health check: {e}"
            logger.error(details)

        return {
            "status": "healthy" if is_ok else "unhealthy",
            "is_simulated": mt5_client.is_simulated,
            "latency_ms": latency_ms,
            "consecutive_failures": self.consecutive_failures,
            "details": details
        }


health_monitor = MT5HealthMonitor()
