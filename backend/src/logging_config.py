"""Centralized logging configuration module.

Configures the Python root logger with rotating file and stdout handlers,
reading all settings from the Settings singleton in src.config.config.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.config import Settings


def setup_logging(config: "Settings | None" = None) -> None:
    """Configure root logger with rotating file and stdout handlers.

    Args:
        config: Settings instance. If None, imports the module-level
                settings singleton from src.config.config.
    """
    if config is None:
        from src.config.config import settings
        config = settings

    log_format = (
        "%(levelname)s: %(asctime)s: %(filename)s: %(funcName)s: %(module)s: %(message)s"
    )
    formatter = logging.Formatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level))

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Silence noisy third-party loggers (Neo4j cartesian product warnings, etc.)
    for noisy_logger in ("neo4j", "neontology", "httpcore", "httpx"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    # Always attach stdout handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # Attempt to create log directory and attach file handler
    log_dir = config.log_dir
    log_path = os.path.join(log_dir, config.log_file)

    try:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=config.log_max_size_mb * 1024 * 1024,
            backupCount=config.log_backup_count,
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except OSError:
        logging.warning(
            "Could not create log directory '%s'; falling back to stdout-only logging.",
            log_dir,
        )
