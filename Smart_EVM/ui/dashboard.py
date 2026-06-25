"""
ui/dashboard.py — Main dashboard page with live counters, charts, and log feed.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QProgressBar,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
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
#  Hold-progress banner                                               #
# ------------------------------------------------------------------ #

class _HoldProgressBar(QFrame):
    """
    Animated 2-second countdown bar shown while the ESP is tracking a held button.
    Hidden when idle; visible and animating during an active hold.
    """

    HOLD_MS = 2000   # must match HOLD_REQUIRED_MS on the ESP

    _ACCENT_COLORS = [
        COLORS["accent"],
        COLORS["accent_green"],
        COLORS["accent_orange"],
        COLORS["accent_red"],
        "#bc8cff",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HoldBar")
        self.setFixedHeight(54)
        self.setStyleSheet(f"""
            QFrame#HoldBar {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(14)

        self._icon = QLabel("⏳")
        self._icon.setFont(QFont("Segoe UI", 14))
        layout.addWidget(self._icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._label = QLabel("Hold to vote…")
        self._label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self._label.setStyleSheet(f"color: {COLORS['text_primary']};")
        text_col.addWidget(self._label)

        self._bar = QProgressBar()
        self._bar.setRange(0, self.HOLD_MS)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(6)
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['bg_secondary']};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {COLORS['accent']};
                border-radius: 3px;
            }}
        """)
        text_col.addWidget(self._bar)
        layout.addLayout(text_col, stretch=1)

        self._pct_lbl = QLabel("0%")
        self._pct_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._pct_lbl.setStyleSheet(f"color: {COLORS['accent']};")
        self._pct_lbl.setFixedWidth(44)
        self._pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._pct_lbl)

        # Internal state
        self._candidate_id = -1
        self._elapsed_ms   = 0

        # Tick timer — advances progress every 40 ms (≈ 25 fps)
        self._tick = QTimer(self)
        self._tick.setInterval(40)
        self._tick.timeout.connect(self._on_tick)

        self.hide()

    # ── Public API ──────────────────────────────────────────────── #

    def start(self, candidate_id: int, name: str) -> None:
        """Show and start animating for the given candidate."""
        self._candidate_id = candidate_id
        self._elapsed_ms   = 0
        color = self._ACCENT_COLORS[(candidate_id - 1) % len(self._ACCENT_COLORS)]

        self._label.setText(f"Holding button for  {name.upper()}…")
        self._label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self._pct_lbl.setStyleSheet(f"color: {color};")
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['bg_secondary']};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
        """)
        self._bar.setValue(0)
        self._pct_lbl.setText("0%")
        self.show()
        self._tick.start()

    def cancel(self) -> None:
        """Hide the bar — hold was released before completing."""
        self._tick.stop()
        self.hide()

    def complete(self) -> None:
        """Flash 100% briefly then hide — vote was confirmed."""
        self._tick.stop()
        self._bar.setValue(self.HOLD_MS)
        self._pct_lbl.setText("100%")
        self._label.setText("✅  Vote confirmed!")
        self._label.setStyleSheet(f"color: {COLORS['accent_green']};")
        self._pct_lbl.setStyleSheet(f"color: {COLORS['accent_green']};")
        # Auto-hide after 800 ms
        QTimer.singleShot(800, self.hide)

    # ── Internal ─────────────────────────────────────────────────── #

    def _on_tick(self) -> None:
        self._elapsed_ms += self._tick.interval()
        clamped = min(self._elapsed_ms, self.HOLD_MS)
        self._bar.setValue(clamped)
        pct = int(clamped * 100 / self.HOLD_MS)
        self._pct_lbl.setText(f"{pct}%")
        if self._elapsed_ms >= self.HOLD_MS:
            # Safety: stop ticking once full — vote packet will call complete()
            self._tick.stop()


# ------------------------------------------------------------------ #
#  Lockout countdown banner                                            #
# ------------------------------------------------------------------ #

class _LockoutBanner(QFrame):
    """
    Real-time countdown shown during the 10-second post-vote lockout.
    Hidden when idle. Shows seconds remaining with a draining progress bar.
    """

    LOCKOUT_MS = 10000   # must match VOTE_LOCKOUT_MS on the ESP

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LockoutBanner")
        self.setFixedHeight(54)
        self._apply_style(locked=True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(14)

        self._icon = QLabel("🔒")
        self._icon.setFont(QFont("Segoe UI", 14))
        layout.addWidget(self._icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        self._label = QLabel("Lockout active")
        self._label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self._label.setStyleSheet(f"color: {COLORS['text_primary']};")
        text_col.addWidget(self._label)

        self._bar = QProgressBar()
        self._bar.setRange(0, self.LOCKOUT_MS)
        self._bar.setValue(self.LOCKOUT_MS)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(6)
        self._bar.setStyleSheet(self._bar_style(COLORS["accent_red"]))
        text_col.addWidget(self._bar)
        layout.addLayout(text_col, stretch=1)

        self._countdown_lbl = QLabel("10s")
        self._countdown_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self._countdown_lbl.setStyleSheet(f"color: {COLORS['accent_red']};")
        self._countdown_lbl.setFixedWidth(48)
        self._countdown_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._countdown_lbl)

        self._elapsed_ms = 0

        self._tick = QTimer(self)
        self._tick.setInterval(100)
        self._tick.timeout.connect(self._on_tick)

        self.hide()

    # ── Public API ──────────────────────────────────────────────── #

    def start_lockout(self) -> None:
        """Begin the 10-second countdown."""
        self._elapsed_ms = 0
        self._bar.setValue(self.LOCKOUT_MS)
        self._bar.setStyleSheet(self._bar_style(COLORS["accent_red"]))
        self._countdown_lbl.setStyleSheet(f"color: {COLORS['accent_red']};")
        self._countdown_lbl.setText("10s")
        self._label.setText("Lockout active — no votes accepted")
        self._icon.setText("🔒")
        self._apply_style(locked=True)
        self.show()
        self._tick.start()

    # ── Internal ─────────────────────────────────────────────────── #

    def _on_tick(self) -> None:
        self._elapsed_ms += self._tick.interval()
        remaining_ms = max(0, self.LOCKOUT_MS - self._elapsed_ms)
        self._bar.setValue(remaining_ms)

        secs_left = (remaining_ms + 999) // 1000   # round up
        self._countdown_lbl.setText(f"{secs_left}s")

        # Colour shifts orange in the last 3 seconds
        if remaining_ms <= 3000:
            color = COLORS["accent_orange"]
            self._bar.setStyleSheet(self._bar_style(color))
            self._countdown_lbl.setStyleSheet(f"color: {color};")

        if self._elapsed_ms >= self.LOCKOUT_MS:
            self._tick.stop()
            self._icon.setText("✅")
            self._label.setText("Ready — lockout cleared")
            self._countdown_lbl.setText("0s")
            self._countdown_lbl.setStyleSheet(f"color: {COLORS['accent_green']};")
            self._bar.setValue(0)
            self._apply_style(locked=False)
            QTimer.singleShot(1200, self.hide)

    @staticmethod
    def _bar_style(color: str) -> str:
        return f"""
            QProgressBar {{
                background: {COLORS['bg_secondary']};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
        """

    def _apply_style(self, locked: bool) -> None:
        border_color = COLORS["accent_red"] if locked else COLORS["accent_green"]
        self.setStyleSheet(f"""
            QFrame#LockoutBanner {{
                background: {COLORS['bg_card']};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)


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
        root.setSpacing(14)

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

        # ── Hold-progress bar (hidden until ESP sends hold_start) ── #
        self._hold_bar = _HoldProgressBar()
        root.addWidget(self._hold_bar)

        # ── Lockout countdown banner (hidden when idle) ─────────── #
        self._lockout_banner = _LockoutBanner()
        root.addWidget(self._lockout_banner)

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

    @pyqtSlot(int)
    def start_hold(self, candidate_id: int) -> None:
        """Show the hold-progress bar for the given candidate."""
        name = self._candidate_map.get(candidate_id, f"Candidate {candidate_id}")
        self._hold_bar.start(candidate_id, name)

    @pyqtSlot(int)
    def cancel_hold(self, candidate_id: int) -> None:
        """Hide the hold-progress bar — button was released too early."""
        self._hold_bar.cancel()

    def complete_hold(self) -> None:
        """Flash 100% and hide — called when vote is confirmed."""
        self._hold_bar.complete()

    def start_lockout(self) -> None:
        """Start the 10-second lockout countdown banner."""
        self._lockout_banner.start_lockout()

    def append_log(self, line: str) -> None:
        """Add a timestamped line to the live events feed."""
        lbl = QLabel(line)
        lbl.setWordWrap(True)

        if "error" in line.lower() or "false" in line.lower():
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
