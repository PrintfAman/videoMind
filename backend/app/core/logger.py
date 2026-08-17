import logging
from logging import Logger
from typing import Any


def get_logger(settings: Any) -> Logger:
    """Create and configure a module-level logger based on settings."""
    logger = logging.getLogger("videomind")
    if not logger.handlers:
        level = logging.DEBUG if getattr(settings, "debug", False) else logging.INFO
        logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
