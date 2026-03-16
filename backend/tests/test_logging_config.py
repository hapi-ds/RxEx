"""Tests for the centralized logging configuration module."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import pytest

from src.config.config import Settings
from src.logging_config import setup_logging


@pytest.fixture(autouse=True)
def _reset_root_logger():
    """Reset root logger handlers before and after each test."""
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    yield
    root.handlers = original_handlers
    root.level = original_level


def test_setup_logging_creates_log_directory(tmp_path: str) -> None:
    """Test that setup_logging creates the log directory if it doesn't exist."""
    log_dir = os.path.join(str(tmp_path), "nested", "logs")
    config = Settings(log_dir=log_dir)
    setup_logging(config)
    assert os.path.isdir(log_dir)


def test_setup_logging_attaches_correct_handlers(tmp_path: str) -> None:
    """Test that setup_logging attaches exactly one RotatingFileHandler and one StreamHandler."""
    config = Settings(log_dir=str(tmp_path))
    setup_logging(config)

    root = logging.getLogger()
    file_handlers = [h for h in root.handlers if isinstance(h, RotatingFileHandler)]
    stream_handlers = [
        h for h in root.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
    ]

    assert len(file_handlers) == 1
    assert len(stream_handlers) == 1


def test_rotating_file_handler_config(tmp_path: str) -> None:
    """Test that RotatingFileHandler is configured with correct maxBytes and backupCount."""
    config = Settings(log_dir=str(tmp_path), log_max_size_mb=5, log_backup_count=3)
    setup_logging(config)

    root = logging.getLogger()
    file_handler = next(h for h in root.handlers if isinstance(h, RotatingFileHandler))

    assert file_handler.maxBytes == 5 * 1024 * 1024
    assert file_handler.backupCount == 3


def test_stream_handler_targets_stdout(tmp_path: str) -> None:
    """Test that StreamHandler targets sys.stdout."""
    config = Settings(log_dir=str(tmp_path))
    setup_logging(config)

    root = logging.getLogger()
    stream_handler = next(
        h for h in root.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
    )

    assert stream_handler.stream is sys.stdout


def test_default_log_level_is_info(tmp_path: str) -> None:
    """Test that default log level is INFO when log_level is unset."""
    config = Settings(log_dir=str(tmp_path))
    setup_logging(config)

    root = logging.getLogger()
    assert root.level == logging.INFO


def test_log_level_applied_from_settings(tmp_path: str) -> None:
    """Test that log level from Settings is applied to root logger."""
    config = Settings(log_dir=str(tmp_path), log_level="DEBUG")
    setup_logging(config)

    root = logging.getLogger()
    assert root.level == logging.DEBUG


def test_log_format_applied(tmp_path: str) -> None:
    """Test that the expected log format is applied to handlers."""
    config = Settings(log_dir=str(tmp_path))
    setup_logging(config)

    expected_format = (
        "%(levelname)s: %(asctime)s: %(filename)s: %(funcName)s: %(module)s: %(message)s"
    )
    root = logging.getLogger()
    for handler in root.handlers:
        assert handler.formatter._fmt == expected_format


def test_clears_existing_handlers(tmp_path: str) -> None:
    """Test that setup_logging clears existing handlers to avoid duplicates."""
    root = logging.getLogger()
    root.addHandler(logging.StreamHandler())
    root.addHandler(logging.StreamHandler())
    assert len(root.handlers) >= 2

    config = Settings(log_dir=str(tmp_path))
    setup_logging(config)

    # Should have exactly 2 handlers: one file, one stream
    assert len(root.handlers) == 2


def test_fallback_to_stdout_on_directory_failure() -> None:
    """Test that setup_logging falls back to stdout-only if log dir creation fails."""
    config = Settings(log_dir="/nonexistent/readonly/path/logs")
    setup_logging(config)

    root = logging.getLogger()
    file_handlers = [h for h in root.handlers if isinstance(h, RotatingFileHandler)]
    stream_handlers = [
        h for h in root.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
    ]

    assert len(file_handlers) == 0
    assert len(stream_handlers) == 1


def test_log_file_receives_messages(tmp_path: str) -> None:
    """Test that log messages are written to the log file."""
    config = Settings(log_dir=str(tmp_path), log_file="test.log")
    setup_logging(config)

    logger = logging.getLogger("test_logger")
    logger.info("hello from test")

    # Flush handlers
    for handler in logging.getLogger().handlers:
        handler.flush()

    log_path = os.path.join(str(tmp_path), "test.log")
    with open(log_path) as f:
        content = f.read()

    assert "hello from test" in content


def test_setup_logging_uses_settings_singleton_when_none() -> None:
    """Test that setup_logging imports the settings singleton when config is None."""
    # This should not raise — it imports and uses the default settings singleton.
    # We just verify it doesn't crash; the fallback path handles missing /app/logs.
    setup_logging(None)

    root = logging.getLogger()
    # Should have at least the stdout handler
    stream_handlers = [
        h for h in root.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
    ]
    assert len(stream_handlers) >= 1
