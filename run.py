import uvicorn
from core import get_logger

logger = get_logger("general")

if __name__ == "__main__":
    logger.info("Starting MT5 AI Auto Trading Platform Server on http://0.0.0.0:8000 ...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
