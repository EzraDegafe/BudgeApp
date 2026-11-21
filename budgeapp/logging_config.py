"""Logging setup: messages go to the terminal and to logs/budgeapp.log.

Each module gets its own logger with `logger = logging.getLogger(__name__)`, so every line shows
which file it came from. Set LOG_LEVEL=DEBUG in .env to see more detail (default: INFO).
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_FILE = LOG_DIR / "budgeapp.log"
FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def setup_logging() -> None:
    """Attach the handlers once. Safe to call on every Streamlit rerun."""
    root = logging.getLogger("budgeapp")
    if root.handlers:
        return  # already set up

    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    root.propagate = False  # don't also print through Streamlit's own logger
    formatter = logging.Formatter(FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    LOG_DIR.mkdir(exist_ok=True)
    # Keeps the newest ~1 MB plus 3 older files, so the logs don't grow forever.
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
