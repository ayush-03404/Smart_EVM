"""
ui/results_page.py — Detailed results table with sortable columns.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from config import COLORS
from database import get_vote_totals, get_total_votes


class ResultsPage(QWidget):
    def __init__(self, candidate_map: dict[int, str], parent=None):
        super().__init__(parent)
        self._candidate_map = candidate_map
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Title
        title_row = QHBoxLayout()
        title = QLabel("Results")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        title_row.addWidget(title)
        title_row.addStretch()

        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.setFixedHeight(32)
        refresh_btn.setStyleSheet(self._btn_style(COLORS["accent"]))
        refresh_btn.clicked.connect(self.refresh)
        title_row.addWidget(refresh_btn)
        layout.addLayout(title_row)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Candidate ID", "Name", "Votes", "Share %"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(self._table_style())
        layout.addWidget(self._table)

        # Footer
        self._footer = QLabel()
        self._footer.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(self._footer)

        self.refresh()

    def refresh(self) -> None:
        totals = get_vote_totals()
        total = get_total_votes()
        self._table.setRowCount(0)
        self._table.setSortingEnabled(False)

        for cid in sorted(self._candidate_map):
            name  = self._candidate_map[cid]
            votes = totals.get(cid, 0)
            share = f"{(votes / total * 100):.1f}%" if total > 0 else "0.0%"

            row = self._table.rowCount()
            self._table.insertRow(row)

            items = [
                QTableWidgetItem(str(cid)),
                QTableWidgetItem(name),
                QTableWidgetItem(str(votes)),
                QTableWidgetItem(share),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 2:  # votes column: highlight leader
                    if votes == max(totals.values(), default=0) and votes > 0:
                        item.setForeground(QColor(COLORS["accent_green"]))
                        item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self._table.setItem(row, col, item)

        self._table.setSortingEnabled(True)
        self._footer.setText(f"Total votes recorded: {total}")

    def update_candidate_names(self, candidate_map: dict[int, str]) -> None:
        self._candidate_map = candidate_map
        self.refresh()

    # ---------------------------------------------------------------- #
    #  Styles                                                            #
    # ---------------------------------------------------------------- #

    @staticmethod
    def _btn_style(color: str) -> str:
        return f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {color};
                color: {color};
                border-radius: 6px;
                padding: 4px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {color}22; }}
        """

    @staticmethod
    def _table_style() -> str:
        return f"""
            QTableWidget {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                color: {COLORS['text_primary']};
                gridline-color: {COLORS['border']};
                font-size: 13px;
                selection-background-color: {COLORS['accent']}33;
            }}
            QHeaderView::section {{
                background: {COLORS['bg_secondary']};
                color: {COLORS['text_muted']};
                padding: 10px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QTableWidget::item {{ padding: 8px; }}
        """
