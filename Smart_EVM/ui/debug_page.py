"""
ui/debug_page.py — In-app Debugging Log page.

Shows all internal application log messages that would previously have
appeared in an external CMD / terminal window.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont

from config import COLORS


class DebugPage(QWidget):
    """Displays all log messages from the application logger."""

    # Colour mapping per log level
    _LEVEL_COLORS = {
        "DEBUG":    "#6e7681",
        "INFO":     "#58a6ff",
        "WARNING":  "#d29922",
        "ERROR":    "#f85149",
        "CRITICAL": "#ff6e6e",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[QLabel] = []
        self._build_ui()

    # ---------------------------------------------------------------- #
    #  UI                                                                #
    # ---------------------------------------------------------------- #

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ---- Title row -------------------------------------------- #
        title_row = QHBoxLayout()
        title = QLabel("Debugging Log")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        title_row.addWidget(title)
        title_row.addStretch()

        self._auto_scroll_chk = QCheckBox("Auto-scroll")
        self._auto_scroll_chk.setChecked(True)
        self._auto_scroll_chk.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        title_row.addWidget(self._auto_scroll_chk)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(30)
        clear_btn.setFixedWidth(70)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                color: {COLORS['text_muted']};
                border-radius: 6px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_red']};
                color: {COLORS['accent_red']};
            }}
        """)
        clear_btn.clicked.connect(self._clear)
        title_row.addWidget(clear_btn)
        root.addLayout(title_row)

        # ---- Info banner ------------------------------------------ #
        info = QLabel(
            "All internal application messages appear here. "
            "No CMD / terminal window will open when you launch the app."
        )
        info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        info.setWordWrap(True)
        root.addWidget(info)

        # ---- Legend ----------------------------------------------- #
        legend_row = QHBoxLayout()
        legend_row.setSpacing(16)
        for level, color in self._LEVEL_COLORS.items():
            dot = QLabel(f"● {level}")
            dot.setStyleSheet(f"color: {color}; font-size: 10px; font-family: 'Consolas', monospace;")
            legend_row.addWidget(dot)
        legend_row.addStretch()
        root.addLayout(legend_row)

        # ---- Log area --------------------------------------------- #
        log_frame = QFrame()
        log_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        log_frame_layout = QVBoxLayout(log_frame)
        log_frame_layout.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {COLORS['bg_secondary']}; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']}; border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._log_layout = QVBoxLayout(self._container)
        self._log_layout.setContentsMargins(14, 10, 14, 10)
        self._log_layout.setSpacing(1)
        self._log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll.setWidget(self._container)
        log_frame_layout.addWidget(self._scroll)
        root.addWidget(log_frame, stretch=1)

        # ---- Status bar ------------------------------------------- #
        self._status_lbl = QLabel("0 messages")
        self._status_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        root.addWidget(self._status_lbl)

    # ---------------------------------------------------------------- #
    #  Public slots                                                      #
    # ---------------------------------------------------------------- #

    @pyqtSlot(str, str)
    def append_entry(self, level: str, line: str) -> None:
        """Receive a log entry (called via Qt signal from logger)."""
        color = self._LEVEL_COLORS.get(level, COLORS["text_muted"])

        lbl = QLabel(line)
        lbl.setFont(QFont("Consolas", 10))
        lbl.setStyleSheet(f"color: {color}; background: transparent; padding: 1px 0;")
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self._log_layout.addWidget(lbl)
        self._entries.append(lbl)

        # Keep max 500 entries to avoid memory growth
        if len(self._entries) > 500:
            oldest = self._entries.pop(0)
            oldest.deleteLater()

        self._status_lbl.setText(f"{len(self._entries)} messages")

        if self._auto_scroll_chk.isChecked():
            # Scroll to bottom
            sb = self._scroll.verticalScrollBar()
            sb.setValue(sb.maximum())

    # ---------------------------------------------------------------- #
    #  Internal                                                          #
    # ---------------------------------------------------------------- #

    def _clear(self) -> None:
        for lbl in self._entries:
            lbl.deleteLater()
        self._entries.clear()
        self._status_lbl.setText("0 messages")
