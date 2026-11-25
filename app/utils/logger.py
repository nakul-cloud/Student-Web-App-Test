import os
import sys
from loguru import logger

logger.remove()

logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# Skip disk file sink on read-only serverless runtimes (e.g. Vercel)
if not os.environ.get("VERCEL"):
    try:
        logger.add(
            "logs/app.log",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name} - {message}",
        )
    except OSError:
        pass
