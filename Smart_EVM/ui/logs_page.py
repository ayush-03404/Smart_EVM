"""
ui/logs_page.py — Full event log viewer with filtering.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QHeaderView, QLineEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from config import COLORS
from database import get_all_events


class LogsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Event Logs")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        title_row.addWidget(title)
        title_row.addStretch()

        # Filter
        self._filter_box = QComboBox()
        self._filter_box.addItems(["All Events", "Votes Only", "Errors Only"])
        self._filter_box.setFixedHeight(32)
        self._filter_box.setStyleSheet(self._combo_style())
        self._filter_box.currentIndexChanged.connect(self.refresh)
        title_row.addWidget(self._filter_box)

        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.setFixedHeight(32)
        refresh_btn.setStyleSheet(self._btn_style(COLORS["accent"]))
        refresh_btn.clicked.connect(self.refresh)
        title_row.addWidget(refresh_btn)
        layout.addLayout(title_row)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["ID", "Timestamp", "Candidate ID", "Candidate Name", "Event Type"])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(self._table_style())
        layout.addWidget(self._table)

        self._count_lbl = QLabel()
        self._count_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(self._count_lbl)

        self.refresh()

    def refresh(self) -> None:
        filter_idx = self._filter_box.currentIndex()
        events = get_all_events()

        if filter_idx == 1:
            events = [e for e in events if e["event_type"] == "vote"]
        elif filter_idx == 2:
            events = [e for e in events if e["event_type"] != "vote"]

        self._table.setRowCount(0)
        for evt in events:
            row = self._table.rowCount()
            self._table.insertRow(row)

            is_vote = evt["event_type"] == "vote"
            color = COLORS["accent_green"] if is_vote else COLORS["accent_red"]

            items = [
                QTableWidgetItem(str(evt["id"])),
                QTableWidgetItem(evt["timestamp"]),
                QTableWidgetItem(str(evt["candidate_id"])),
                QTableWidgetItem(evt["candidate_name"]),
                QTableWidgetItem(evt["event_type"].upper()),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 4:
                    item.setForeground(QColor(color))
                    item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                self._table.setItem(row, col, item)

        self._count_lbl.setText(f"Showing {len(events)} record(s)")

    # ---------------------------------------------------------------- #

    @staticmethod
    def _btn_style(color: str) -> str:
        return f"""
            QPushButton {{
                background: transparent; border: 1px solid {color};
                color: {color}; border-radius: 6px; padding: 4px 14px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {color}22; }}
        """

    @staticmethod
    def _combo_style() -> str:
        return f"""
            QComboBox {{
                background: {COLORS['bg_card']}; border: 1px solid {COLORS['border']};
                color: {COLORS['text_primary']}; border-radius: 6px; padding: 4px 10px; font-size: 12px;
            }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox QAbstractItemView {{
                background: {COLORS['bg_card']}; border: 1px solid {COLORS['border']};
                color: {COLORS['text_primary']}; selection-background-color: {COLORS['accent']}33;
            }}
        """

    @staticmethod
    def _table_style() -> str:
        return f"""
            QTableWidget {{
                background: {COLORS['bg_card']}; border: 1px solid {COLORS['border']};
                border-radius: 8px; color: {COLORS['text_primary']};
                gridline-color: {COLORS['border']}; font-size: 12px;
                selection-background-color: {COLORS['accent']}33;
            }}
            QHeaderView::section {{
                background: {COLORS['bg_secondary']}; color: {COLORS['text_muted']};
                padding: 10px; border: none; border-bottom: 1px solid {COLORS['border']};
                font-size: 11px; font-weight: 600;
            }}
            QTableWidget::item {{ padding: 6px; }}
        """
