"""
ui/settings_page.py — Candidate name editor, display options, and session controls.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config import COLORS, WS_PORT
from database import clear_all


class SettingsPage(QWidget):
    names_changed      = pyqtSignal(dict)   # {int: str}
    session_cleared    = pyqtSignal()
    fullscreen_requested = pyqtSignal(bool) # True = enter, False = exit

    def __init__(self, candidate_map: dict[int, str], parent=None):
        super().__init__(parent)
        self._candidate_map = dict(candidate_map)
        self._inputs: dict[int, QLineEdit] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        # Outer scroll so all cards are reachable on smaller screens
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # ── Candidate name editor ─────────────────────────────────── #
        cand_card = self._card()
        cand_layout = QVBoxLayout(cand_card)
        cand_layout.setContentsMargins(20, 20, 20, 20)
        cand_layout.setSpacing(12)

        sec_title = QLabel("Candidate Names")
        sec_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: 600;")
        cand_layout.addWidget(sec_title)

        sub = QLabel("Edit the names mapped to each hardware candidate button (1, 2, 3, 4).")
        sub.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        cand_layout.addWidget(sub)

        accent_colors = [
            COLORS["accent"], COLORS["accent_green"],
            COLORS["accent_orange"], COLORS["accent_red"], "#bc8cff",
        ]

        for cid in sorted(self._candidate_map):
            row = QHBoxLayout()
            badge = QLabel(f"  {cid}  ")
            badge.setFixedWidth(32)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(f"""
                background: {accent_colors[(cid-1) % len(accent_colors)]};
                color: #000; border-radius: 4px; font-weight: 700; font-size: 11px;
            """)
            row.addWidget(badge)

            inp = QLineEdit(self._candidate_map.get(cid, f"Candidate {cid}"))
            inp.setFixedHeight(34)
            inp.setStyleSheet(self._input_style())
            self._inputs[cid] = inp
            row.addWidget(inp)
            cand_layout.addLayout(row)

        save_btn = QPushButton("Save Names")
        save_btn.setFixedHeight(36)
        save_btn.setStyleSheet(self._btn_style(COLORS["accent"]))
        save_btn.clicked.connect(self._save_names)
        cand_layout.addWidget(save_btn)

        layout.addWidget(cand_card)

        # ── Display / Full Screen ─────────────────────────────────── #
        disp_card = self._card()
        disp_layout = QVBoxLayout(disp_card)
        disp_layout.setContentsMargins(20, 20, 20, 20)
        disp_layout.setSpacing(12)

        disp_title = QLabel("Display")
        disp_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: 600;")
        disp_layout.addWidget(disp_title)

        disp_sub = QLabel("Switch the application between windowed and full screen mode.")
        disp_sub.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        disp_layout.addWidget(disp_sub)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        enter_fs_btn = QPushButton("⛶  Enter Full Screen")
        enter_fs_btn.setFixedHeight(38)
        enter_fs_btn.setStyleSheet(self._btn_style(COLORS["accent_green"]))
        enter_fs_btn.clicked.connect(lambda: self.fullscreen_requested.emit(True))
        btn_row.addWidget(enter_fs_btn)

        exit_fs_btn = QPushButton("⊡  Exit Full Screen")
        exit_fs_btn.setFixedHeight(38)
        exit_fs_btn.setStyleSheet(self._btn_style(COLORS["accent_orange"]))
        exit_fs_btn.clicked.connect(lambda: self.fullscreen_requested.emit(False))
        btn_row.addWidget(exit_fs_btn)

        btn_row.addStretch()
        disp_layout.addLayout(btn_row)

        tip = QLabel("Tip: press the Esc key to exit full screen at any time.")
        tip.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        disp_layout.addWidget(tip)

        layout.addWidget(disp_card)

        # ── Network info ──────────────────────────────────────────── #
        net_card = self._card()
        net_layout = QVBoxLayout(net_card)
        net_layout.setContentsMargins(20, 20, 20, 20)
        net_layout.setSpacing(8)

        net_title = QLabel("Network Configuration")
        net_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: 600;")
        net_layout.addWidget(net_title)

        for label, value in [
            ("WebSocket Port",         str(WS_PORT)),
            ("ESP8266 SoftAP SSID",    "SMART_EVM"),
            ("ESP8266 SoftAP Password","12345678"),
            ("ESP8266 IP",             "192.168.4.1"),
            ("PC IP (assigned by ESP)","192.168.4.2"),
        ]:
            r = QHBoxLayout()
            k = QLabel(label + ":")
            k.setFixedWidth(220)
            k.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
            v = QLabel(value)
            v.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; font-weight: 600;")
            r.addWidget(k)
            r.addWidget(v)
            r.addStretch()
            net_layout.addLayout(r)

        layout.addWidget(net_card)

        # ── Danger zone ───────────────────────────────────────────── #
        danger_card = self._card(border_color=COLORS["accent_red"] + "55")
        danger_layout = QVBoxLayout(danger_card)
        danger_layout.setContentsMargins(20, 20, 20, 20)
        danger_layout.setSpacing(10)

        danger_title = QLabel("Danger Zone")
        danger_title.setStyleSheet(f"color: {COLORS['accent_red']}; font-size: 13px; font-weight: 600;")
        danger_layout.addWidget(danger_title)

        clear_row = QHBoxLayout()
        clear_desc = QLabel("Delete all vote records and start a fresh election session.")
        clear_desc.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        clear_row.addWidget(clear_desc)
        clear_row.addStretch()
        clear_btn = QPushButton("Clear All Data")
        clear_btn.setFixedHeight(34)
        clear_btn.setStyleSheet(self._btn_style(COLORS["accent_red"]))
        clear_btn.clicked.connect(self._clear_session)
        clear_row.addWidget(clear_btn)
        danger_layout.addLayout(clear_row)

        layout.addWidget(danger_card)
        layout.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll)

    # ---------------------------------------------------------------- #
    #  Slots                                                             #
    # ---------------------------------------------------------------- #

    def _save_names(self) -> None:
        for cid, inp in self._inputs.items():
            name = inp.text().strip() or f"Candidate {cid}"
            self._candidate_map[cid] = name
        self.names_changed.emit(dict(self._candidate_map))
        QMessageBox.information(self, "Saved", "Candidate names updated successfully.")

    def _clear_session(self) -> None:
        reply = QMessageBox.question(
            self, "Clear All Data",
            "This will permanently delete ALL vote records.\nAre you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            clear_all()
            self.session_cleared.emit()
            QMessageBox.information(self, "Done", "All data cleared. New session started.")

    # ---------------------------------------------------------------- #
    #  Helpers                                                           #
    # ---------------------------------------------------------------- #

    @staticmethod
    def _card(border_color: str = COLORS["border"]) -> QFrame:
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)
        return f

    @staticmethod
    def _input_style() -> str:
        return f"""
            QLineEdit {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                color: {COLORS['text_primary']};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {COLORS['accent']}; }}
        """

    @staticmethod
    def _btn_style(color: str) -> str:
        return f"""
            QPushButton {{
                background: {color}22;
                border: 1px solid {color};
                color: {color};
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {color}44; }}
        """
