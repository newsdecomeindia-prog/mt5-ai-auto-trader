import os
import sys
from pathlib import Path
from loguru import logger

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure Loguru format
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# Remove default handler
logger.remove()

# Console logger
logger.add(
    sys.stdout,
    format=LOG_FORMAT,
    level="INFO",
    colorize=True,
)

# General log file
logger.add(
    LOGS_DIR / "app.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="10 MB",
    retention="14 days",
    compression="zip",
)

# Categorized log files
logger.add(
    LOGS_DIR / "connection.log",
    format=LOG_FORMAT,
    filter=lambda record: "connection" in record["extra"].get("category", "").lower(),
    level="INFO",
    rotation="5 MB",
    retention="7 days",
)

logger.add(
    LOGS_DIR / "trading.log",
    format=LOG_FORMAT,
    filter=lambda record: "trading" in record["extra"].get("category", "").lower(),
    level="INFO",
    rotation="10 MB",
    retention="14 days",
)

logger.add(
    LOGS_DIR / "risk.log",
    format=LOG_FORMAT,
    filter=lambda record: "risk" in record["extra"].get("category", "").lower(),
    level="INFO",
    rotation="5 MB",
    retention="14 days",
)

logger.add(
    LOGS_DIR / "api.log",
    format=LOG_FORMAT,
    filter=lambda record: "api" in record["extra"].get("category", "").lower(),
    level="INFO",
    rotation="5 MB",
    retention="7 days",
)

logger.add(
    LOGS_DIR / "error.log",
    format=LOG_FORMAT,
    level="ERROR",
    rotation="10 MB",
    retention="30 days",
    backtrace=True,
    diagnose=True,
)


def get_logger(category: str = "general"):
    """
    Returns a bound logger with a specific category for targeted log file routing.
    """
    return logger.bind(category=category)


__all__ = ["logger", "get_logger"]
