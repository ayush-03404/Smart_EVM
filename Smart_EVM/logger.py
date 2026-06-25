"""
logger.py — Centralised application logger that emits Qt signals
so log messages can be consumed by the UI without threading issues.

Console output is intentionally suppressed — all output is routed to
the in-app Debugging Log page instead of an external CMD window.
"""

import logging
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal


class _LogSignalEmitter(QObject):
    """Internal singleton that carries log signals."""
    # Compact line for the dashboard live events feed
    new_log = pyqtSignal(str)
    # Rich entry for the Debugging Log page: (level_name, formatted_line)
    new_debug_log = pyqtSignal(str, str)


_emitter: _LogSignalEmitter | None = None


def get_emitter() -> _LogSignalEmitter:
    global _emitter
    if _emitter is None:
        _emitter = _LogSignalEmitter()
    return _emitter


class _QtHandler(logging.Handler):
    """Logging handler that forwards records to Qt signals only (no console)."""

    def emit(self, record: logging.LogRecord) -> None:
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        short_line = f"[{ts}] {record.getMessage()}"
        full_line  = f"[{ts}] [{record.levelname}]  {record.getMessage()}"
        emitter = get_emitter()
        emitter.new_log.emit(short_line)
        emitter.new_debug_log.emit(record.levelname, full_line)


# Build the root logger once
_root_logger = logging.getLogger("smart_evm")
_root_logger.setLevel(logging.DEBUG)

# ONLY the Qt signal handler — no console / StreamHandler
# (all output surfaces in the in-app Debugging Log page)
_qt_handler = _QtHandler()
_root_logger.addHandler(_qt_handler)


def get_logger(name: str = "smart_evm") -> logging.Logger:
    """Return a named child of the application logger."""
    return logging.getLogger(name)
