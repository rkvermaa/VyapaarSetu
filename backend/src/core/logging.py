"""Structured logging using loguru."""

import sys
from loguru import logger

from src.config import settings


def setup_logging() -> None:
    """Configure loguru based on settings."""
    logger.remove()

    fmt = settings.get("LOG_FORMAT", "pretty")
    level = settings.get("LOG_LEVEL", "INFO")

    if fmt == "json":
        logger.add(
            sys.stdout,
            level=level,
            serialize=True,
            backtrace=False,
            diagnose=False,
        )
    else:
        logger.add(
            sys.stdout,
            level=level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
                "<level>{message}</level>"
            ),
            colorize=True,
        )


log = logger
