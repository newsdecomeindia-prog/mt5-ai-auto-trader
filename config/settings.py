from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # MT5 Settings
    MT5_LOGIN: int = Field(default=0, description="MT5 Account Login Number")
    MT5_PASSWORD: str = Field(default="", description="MT5 Account Password")
    MT5_SERVER: str = Field(default="", description="MT5 Broker Server Name")
    MT5_PATH: Optional[str] = Field(default=None, description="Path to terminal64.exe")

    # Database Settings
    DATABASE_URL: str = Field(default="sqlite:///mt5_trading.db", description="Database connection URL")

    # Telegram Settings
    TELEGRAM_TOKEN: str = Field(default="", description="Telegram Bot API Token")
    TELEGRAM_CHAT_ID: str = Field(default="", description="Telegram Chat ID for alerts")

    # Risk & Execution Defaults
    RISK_PERCENT: float = Field(default=1.0, description="Risk percentage per trade")
    DEFAULT_LOT: float = Field(default=0.1, description="Default fixed lot size")
    MAGIC_NUMBER: int = Field(default=202501, description="MT5 Expert Magic Number")

    # Platform Operation Settings
    PAPER_TRADING: bool = Field(default=True, description="Enable paper trading / simulated execution fallback")
    POLL_INTERVAL_SECONDS: int = Field(default=5, description="Main loop scan interval in seconds")
    MAX_OPEN_TRADES: int = Field(default=5, description="Maximum allowed simultaneous open trades")
    DAILY_LOSS_LIMIT_PERCENT: float = Field(default=5.0, description="Daily max drawdown limit percentage")
    DAILY_PROFIT_TARGET_PERCENT: float = Field(default=10.0, description="Daily profit target percentage")
    MAX_SPREAD_PIPS: float = Field(default=3.0, description="Maximum allowed spread in pips")


settings = Settings()
