from __future__ import annotations

import sys
from typing import Any, Dict

from loguru import logger

from app.core.settings import settings


def configure_logging() -> None:
    logger.remove()

    config: Dict[str, Any] = {
        "sink": sys.stdout,
        "colorize": True,
        "level": settings.log_level,
        "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
    }
    logger.add(**config)
