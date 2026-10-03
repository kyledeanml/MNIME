"""Application logging: rotating file in %LOCALAPPDATA%\\MNIME\\logs plus stderr in dev."""

import logging
import logging.handlers
import os
import sys

_CONFIGURED = False


def get_log_dir() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "MNIME", "logs")
    os.makedirs(path, exist_ok=True)
    return path


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure the 'mnime' logger once. Safe to call repeatedly."""
    global _CONFIGURED
    logger = logging.getLogger("mnime")
    if _CONFIGURED:
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    try:
        fh = logging.handlers.RotatingFileHandler(
            os.path.join(get_log_dir(), "mnime.log"),
            maxBytes=1_000_000, backupCount=3, encoding="utf-8",
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        pass  # Logging must never prevent the app from starting

    if not getattr(sys, "frozen", False):
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    _CONFIGURED = True
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger such as 'mnime.pdf_engine'."""
    return logging.getLogger(f"mnime.{name}")
