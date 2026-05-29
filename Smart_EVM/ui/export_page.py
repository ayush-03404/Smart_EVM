"""
ui/export_page.py — Excel export interface.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QFileDialog, QMessageBox,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from config import COLORS, EXPORT_PATH
from excel_export import export
from database import get_total_votes


class _ExportWorker(QThread):
    done   = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, candidate_map: dict, out_path: str):
        super().__init__()
        self._map = candidate_map
        self._path = out_path

    def run(self) -> None:
        try:
            path = export(self._map, self._path)
            self.done.emit(path)
        except Exception as exc:
            self.failed.emit(str(exc))


class ExportPage(QWidget):
    def __init__(self, candidate_map: dict[int, str], parent=None):
        super().__init__(parent)
        self._candidate_map = candidate_map
        self._worker: _ExportWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Export")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # Info card
        card = self._card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(14)

        icon_lbl = QLabel("📊")
        icon_lbl.setFont(QFont("Segoe UI", 40))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_lbl)

        h = QLabel("Export Results to Excel")
        h.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.setStyleSheet(f"color: {COLORS['text_primary']};")
        card_layout.addWidget(h)

        desc = QLabel(
            "Generates a professional .xlsx report containing:\n"
            "  •  Vote totals per candidate\n"
            "  •  Bar chart and pie chart\n"
            "  •  Full timestamped event log"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; line-height: 1.6;")
        card_layout.addWidget(desc)

        self._votes_lbl = QLabel()
        self._votes_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._votes_lbl.setStyleSheet(f"color: {COLORS['accent']}; font-size: 12px; font-weight: 600;")
        card_layout.addWidget(self._votes_lbl)

        # Path row
        path_row = QHBoxLayout()
        self._path_lbl = QLabel(os.path.abspath(EXPORT_PATH))
        self._path_lbl.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 11px;
            font-family: 'Consolas', monospace;
        """)
        self._path_lbl.setWordWrap(True)
        path_row.addWidget(self._path_lbl)

        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedHeight(34)
        browse_btn.setStyleSheet(self._btn_style(COLORS["text_muted"]))
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(browse_btn)
        card_layout.addLayout(path_row)

        # Progress bar (hidden by default)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)   # indeterminate
        self._progress.setFixedHeight(4)
        self._progress.setVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background: {COLORS['border']}; border-radius: 2px; }}
            QProgressBar::chunk {{ background: {COLORS['accent']}; border-radius: 2px; }}
        """)
        card_layout.addWidget(self._progress)

        # Export button
        self._export_btn = QPushButton("Export to Excel")
        self._export_btn.setFixedHeight(42)
        self._export_btn.setStyleSheet(self._btn_style(COLORS["accent_green"], solid=True))
        self._export_btn.clicked.connect(self._do_export)
        card_layout.addWidget(self._export_btn)

        layout.addWidget(card)
        layout.addStretch()
        self._update_vote_count()

    # ---------------------------------------------------------------- #

    def _update_vote_count(self) -> None:
        self._votes_lbl.setText(f"{get_total_votes()} vote(s) will be exported")

    def _browse(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Excel File", EXPORT_PATH, "Excel Files (*.xlsx)")
        if path:
            self._path_lbl.setText(os.path.abspath(path))

    def _do_export(self) -> None:
        self._update_vote_count()
        out_path = self._path_lbl.text()
        self._export_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._worker = _ExportWorker(self._candidate_map, out_path)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_fail)
        self._worker.start()

    def _on_done(self, path: str) -> None:
        self._progress.setVisible(False)
        self._export_btn.setEnabled(True)
        QMessageBox.information(self, "Export Complete", f"File saved to:\n{path}")

    def _on_fail(self, msg: str) -> None:
        self._progress.setVisible(False)
        self._export_btn.setEnabled(True)
        QMessageBox.critical(self, "Export Failed", f"Error: {msg}")

    def update_candidate_names(self, candidate_map: dict[int, str]) -> None:
        self._candidate_map = candidate_map

    # ---------------------------------------------------------------- #

    @staticmethod
    def _card() -> QFrame:
        f = QFrame()
        f.setMaximumWidth(680)
        f.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        return f

    @staticmethod
    def _btn_style(color: str, solid: bool = False) -> str:
        if solid:
            return f"""
                QPushButton {{
                    background: {color};
                    border: none;
                    color: #000;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 700;
                }}
                QPushButton:hover {{ background: {color}cc; }}
                QPushButton:disabled {{ background: {COLORS['border']}; color: {COLORS['text_muted']}; }}
            """
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
