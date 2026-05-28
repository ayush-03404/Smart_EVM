"""
logger.py — Centralised application logger that emits Qt signals
so log messages can be consumed by the UI without threading issues.
"""

import logging
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal


class _LogSignalEmitter(QObject):
    """Internal singleton that carries the log signal."""
    new_log = pyqtSignal(str)   # formatted log line


_emitter: _LogSignalEmitter | None = None


def get_emitter() -> _LogSignalEmitter:
    global _emitter
    if _emitter is None:
        _emitter = _LogSignalEmitter()
    return _emitter


class _QtHandler(logging.Handler):
    """Logging handler that forwards records to the Qt signal."""

    def emit(self, record: logging.LogRecord) -> None:
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        line = f"[{ts}] {record.getMessage()}"
        get_emitter().new_log.emit(line)


# Build the root logger once
_root_logger = logging.getLogger("smart_evm")
_root_logger.setLevel(logging.DEBUG)

# Console handler (always useful for debugging)
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)s  %(message)s"))
_root_logger.addHandler(_console_handler)

# Qt signal handler
_qt_handler = _QtHandler()
_root_logger.addHandler(_qt_handler)


def get_logger(name: str = "smart_evm") -> logging.Logger:
    """Return a named child of the application logger."""
    return logging.getLogger(name)
