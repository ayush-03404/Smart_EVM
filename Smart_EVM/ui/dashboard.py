"""
ui/dashboard.py — Main dashboard page with live counters, charts, and log feed.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from config import COLORS, DEFAULT_CANDIDATES
from charts import BarChartWidget, PieChartWidget
from database import get_vote_totals, get_total_votes


# ------------------------------------------------------------------ #
#  Reusable card widget                                                #
# ------------------------------------------------------------------ #

class _Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setStyleSheet(f"""
            QFrame#Card {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)


class VoteCard(_Card):
    """Single candidate vote counter card."""

    def __init__(self, candidate_id: int, candidate_name: str, parent=None):
        super().__init__(parent)
        self.candidate_id = candidate_id

        accent_colors = [
            COLORS["accent"],
            COLORS["accent_green"],
            COLORS["accent_orange"],
            COLORS["accent_red"],
            "#bc8cff",
        ]
        color = accent_colors[(candidate_id - 1) % len(accent_colors)]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        bar = QLabel()
        bar.setFixedHeight(3)
        bar.setStyleSheet(f"background: {color}; border-radius: 2px;")
        layout.addWidget(bar)

        self._name_lbl = QLabel(candidate_name.upper())
        self._name_lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: 600; letter-spacing: 1px;"
        )
        layout.addWidget(self._name_lbl)

        self._count_lbl = QLabel("0")
        self._count_lbl.setStyleSheet(
            f"color: {color}; font-size: 36px; font-weight: 700;"
        )
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._count_lbl)

        votes_lbl = QLabel("votes")
        votes_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(votes_lbl)

    def set_count(self, n: int) -> None:
        self._count_lbl.setText(str(n))

    def set_name(self, name: str) -> None:
        self._name_lbl.setText(name.upper())


# ------------------------------------------------------------------ #
#  Dashboard page                                                      #
# ------------------------------------------------------------------ #

class DashboardPage(QWidget):
    def __init__(self, candidate_map: dict[int, str], parent=None):
        super().__init__(parent)
        self._candidate_map = candidate_map
        self._vote_cards: dict[int, VoteCard] = {}

        self._build_ui()

        # Periodic background refresh every 2 seconds
        # (votes also trigger an immediate refresh via _on_vote in main.py)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start(2000)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(20)

        # ── Title row ──────────────────────────────────────────── #
        title_row = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        title_row.addWidget(title)
        title_row.addStretch()

        self._total_lbl = QLabel("Total Votes: 0")
        self._total_lbl.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 13px;
            font-weight: 600;
        """)
        title_row.addWidget(self._total_lbl)
        root.addLayout(title_row)

        # ── Candidate cards ────────────────────────────────────── #
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        for cid, name in sorted(self._candidate_map.items()):
            card = VoteCard(cid, name)
            card.setFixedHeight(130)
            self._vote_cards[cid] = card
            cards_row.addWidget(card)
        root.addLayout(cards_row)

        # ── Charts + log feed ──────────────────────────────────── #
        mid_row = QHBoxLayout()
        mid_row.setSpacing(14)

        # Bar chart
        bar_card = _Card()
        bar_layout = QVBoxLayout(bar_card)
        bar_layout.setContentsMargins(12, 12, 12, 8)
        self._bar_chart = BarChartWidget()
        bar_layout.addWidget(self._bar_chart)
        mid_row.addWidget(bar_card, stretch=5)

        # Pie chart
        pie_card = _Card()
        pie_layout = QVBoxLayout(pie_card)
        pie_layout.setContentsMargins(12, 12, 12, 8)
        self._pie_chart = PieChartWidget()
        pie_layout.addWidget(self._pie_chart)
        mid_row.addWidget(pie_card, stretch=4)

        # Live events log
        log_card = _Card()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(12, 12, 12, 8)
        log_title = QLabel("Live Events")
        log_title.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-weight: 600; font-size: 12px;"
        )
        log_layout.addWidget(log_title)

        self._log_area = QScrollArea()
        self._log_area.setWidgetResizable(True)
        self._log_area.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {COLORS['bg_secondary']}; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']}; border-radius: 3px;
            }}
        """)
        self._log_inner = QWidget()
        self._log_vbox = QVBoxLayout(self._log_inner)
        self._log_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._log_vbox.setSpacing(2)
        self._log_area.setWidget(self._log_inner)
        log_layout.addWidget(self._log_area)
        mid_row.addWidget(log_card, stretch=3)

        root.addLayout(mid_row)

        # ── "Made by" footer ───────────────────────────────────── #
        footer = QLabel("Made by — Ayush Raj,  8-ICSE")
        footer.setAlignment(Qt.AlignmentFlag.AlignRight)
        footer.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; padding-top: 2px;"
        )
        root.addWidget(footer)

        self.refresh()

    # ---------------------------------------------------------------- #
    #  Public API                                                        #
    # ---------------------------------------------------------------- #

    def refresh(self) -> None:
        """Pull latest totals from DB and redraw — called immediately on every vote."""
        totals = get_vote_totals()
        for cid, card in self._vote_cards.items():
            card.set_count(totals.get(cid, 0))
            card.set_name(self._candidate_map.get(cid, f"C{cid}"))
        self._total_lbl.setText(f"Total Votes: {get_total_votes()}")
        self._bar_chart.update_data(self._candidate_map, totals)
        self._pie_chart.update_data(self._candidate_map, totals)

    def update_candidate_names(self, candidate_map: dict[int, str]) -> None:
        self._candidate_map = candidate_map
        self.refresh()

    def append_log(self, line: str) -> None:
        """Add a timestamped line to the live events feed."""
        lbl = QLabel(line)
        lbl.setWordWrap(True)

        if "error" in line.lower():
            color = COLORS["accent_red"]
        elif "vote" in line.lower():
            color = COLORS["accent_green"]
        else:
            color = COLORS["text_muted"]

        lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; font-family: 'Consolas', monospace;"
        )
        # Insert newest at top
        self._log_vbox.insertWidget(0, lbl)

        # Keep only last 100 entries
        while self._log_vbox.count() > 100:
            item = self._log_vbox.takeAt(self._log_vbox.count() - 1)
            if item.widget():
                item.widget().deleteLater()
