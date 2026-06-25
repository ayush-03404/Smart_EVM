"""
main.py — Application entry point.

Builds the main window with sidebar navigation, starts the WebSocket
server, wires all signals, and launches the Qt event loop.
"""

import sys
import os
import subprocess

# -----------------------------------------------------------------------
# CRITICAL — fix working directory BEFORE anything else.
# -----------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(_HERE)
sys.path.insert(0, _HERE)

# -----------------------------------------------------------------------
# Also activate .venv site-packages if present (used by launch.pyw)
# -----------------------------------------------------------------------
_venv_site = os.path.join(_HERE, ".venv", "Lib", "site-packages")
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(0, _venv_site)

# -----------------------------------------------------------------------
# AUTO-INSTALL — installs only missing packages, fast on subsequent runs.
# -----------------------------------------------------------------------
_REQUIRED = {
    "PyQt6":      "PyQt6",
    "websockets": "websockets",
    "openpyxl":   "openpyxl",
    "matplotlib": "matplotlib",
}

def _check_and_install() -> None:
    missing = []
    for module, pkg in _REQUIRED.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(pkg)

    if not missing:
        return

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
        check=False,
    )
    if result.returncode != 0:
        sys.exit(1)

_check_and_install()

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QIcon

from config import COLORS, DEFAULT_CANDIDATES, APP_NAME, APP_VERSION
from database import init_db, record_vote
from logger import get_logger, get_emitter
from websocket_server import WebSocketServer
from ui.dashboard import DashboardPage
from ui.results_page import ResultsPage
from ui.logs_page import LogsPage
from ui.settings_page import SettingsPage
from ui.export_page import ExportPage
from ui.debug_page import DebugPage

log = get_logger("smart_evm.main")


# ------------------------------------------------------------------ #
#  Sidebar button                                                      #
# ------------------------------------------------------------------ #

class SidebarButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(f"  {icon}  {label}", parent)
        self.setCheckable(True)
        self.setFixedHeight(44)
        self.setFont(QFont("Segoe UI", 11))
        self._update_style(False)

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        self._update_style(checked)

    def _update_style(self, active: bool) -> None:
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['accent']}18;
                    border: none;
                    border-left: 3px solid {COLORS['accent']};
                    color: {COLORS['accent']};
                    text-align: left;
                    padding-left: 14px;
                    border-radius: 0;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-left: 3px solid transparent;
                    color: {COLORS['text_muted']};
                    text-align: left;
                    padding-left: 14px;
                    border-radius: 0;
                }}
                QPushButton:hover {{
                    background: {COLORS['bg_secondary']};
                    color: {COLORS['text_primary']};
                }}
            """)


# ------------------------------------------------------------------ #
#  Status bar indicator                                                #
# ------------------------------------------------------------------ #

class _StatusDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._dot = QLabel("●")
        self._dot.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self._dot)

        self._text = QLabel("Server starting…")
        self._text.setFont(QFont("Segoe UI", 10))
        self._text.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(self._text)

        self.set_offline()

    def set_starting(self) -> None:
        self._dot.setStyleSheet(f"color: {COLORS['accent_orange']};")
        self._text.setText("Server starting…")

    def set_online(self, port: int) -> None:
        self._dot.setStyleSheet(f"color: {COLORS['accent_green']};")
        self._text.setText(f"Server listening on :{port}")

    def set_offline(self) -> None:
        self._dot.setStyleSheet(f"color: {COLORS['accent_red']};")
        self._text.setText("Server offline")

    def set_esp_connected(self, addr: str) -> None:
        self._dot.setStyleSheet(f"color: {COLORS['accent_green']};")
        self._text.setText(f"ESP connected  {addr}")

    def set_esp_disconnected(self) -> None:
        self._dot.setStyleSheet(f"color: {COLORS['accent_orange']};")
        self._text.setText("ESP disconnected — waiting…")


# ------------------------------------------------------------------ #
#  Main window                                                         #
# ------------------------------------------------------------------ #

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._candidate_map: dict[int, str] = dict(DEFAULT_CANDIDATES)
        self._ws_server = WebSocketServer(self)

        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.resize(1280, 760)
        self.setMinimumSize(960, 620)

        self._apply_global_style()
        self._build_ui()
        self._connect_signals()
        self._start_server()

        log.info("SMART EVM started — version %s", APP_VERSION)

    # ---------------------------------------------------------------- #
    #  UI construction                                                   #
    # ---------------------------------------------------------------- #

    def _apply_global_style(self) -> None:
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
                font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif;
            }}
            QScrollBar:vertical {{
                background: {COLORS['bg_secondary']}; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']}; border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QMessageBox {{ background: {COLORS['bg_card']}; }}
            QMessageBox QLabel {{ color: {COLORS['text_primary']}; }}
            QMessageBox QPushButton {{
                background: {COLORS['accent']}22; border: 1px solid {COLORS['accent']};
                color: {COLORS['accent']}; border-radius: 6px; padding: 4px 16px;
            }}
        """)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ─────────────────────────────────────────────── #
        sidebar = QWidget()
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet(
            f"background: {COLORS['bg_sidebar']}; border-right: 1px solid {COLORS['border']};"
        )
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Logo
        logo_widget = QWidget()
        logo_widget.setFixedHeight(60)
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(16, 0, 16, 0)
        app_name_lbl = QLabel(f"⚡ {APP_NAME}")
        app_name_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        app_name_lbl.setStyleSheet(f"color: {COLORS['accent']};")
        logo_layout.addWidget(app_name_lbl)
        sb_layout.addWidget(logo_widget)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        sb_layout.addWidget(sep)
        sb_layout.addSpacing(8)

        # Navigation
        nav_items = [
            ("dashboard_btn", "🏠", "Dashboard"),
            ("results_btn",   "📊", "Results"),
            ("logs_btn",      "📋", "Logs"),
            ("settings_btn",  "⚙️",  "Settings"),
            ("export_btn",    "📤", "Export"),
            ("debug_btn",     "🔧", "Debugging Log"),
        ]
        self._nav_buttons: list[SidebarButton] = []
        for attr, icon, label in nav_items:
            btn = SidebarButton(icon, label)
            btn.clicked.connect(lambda _, a=attr: self._navigate(a))
            setattr(self, attr, btn)
            self._nav_buttons.append(btn)
            sb_layout.addWidget(btn)

        sb_layout.addStretch()

        # "Made by" credit
        made_by_lbl = QLabel("Made by — Ayush Raj\n8-ICSE")
        made_by_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        made_by_lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; padding: 6px 8px;"
        )
        sb_layout.addWidget(made_by_lbl)

        # Version
        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_lbl.setStyleSheet(f"color: {COLORS['border']}; font-size: 10px; padding: 4px;")
        sb_layout.addWidget(ver_lbl)

        root.addWidget(sidebar)

        # ── Content area ─────────────────────────────────────────── #
        content_wrapper = QVBoxLayout()
        content_wrapper.setContentsMargins(0, 0, 0, 0)
        content_wrapper.setSpacing(0)

        # Top bar
        top_bar = QWidget()
        top_bar.setFixedHeight(48)
        top_bar.setStyleSheet(f"""
            background: {COLORS['bg_secondary']};
            border-bottom: 1px solid {COLORS['border']};
        """)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(20, 0, 20, 0)

        self._page_title = QLabel("Dashboard")
        self._page_title.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self._page_title.setStyleSheet(f"color: {COLORS['text_primary']};")
        top_bar_layout.addWidget(self._page_title)
        top_bar_layout.addStretch()

        self._status_dot = _StatusDot()
        top_bar_layout.addWidget(self._status_dot)
        content_wrapper.addWidget(top_bar)

        # Pages
        self._stack = QStackedWidget()
        self._dashboard = DashboardPage(self._candidate_map)
        self._results   = ResultsPage(self._candidate_map)
        self._logs      = LogsPage()
        self._settings  = SettingsPage(self._candidate_map)
        self._export    = ExportPage(self._candidate_map)
        self._debug     = DebugPage()

        for page in (
            self._dashboard, self._results, self._logs,
            self._settings, self._export, self._debug,
        ):
            self._stack.addWidget(page)

        content_wrapper.addWidget(self._stack)

        content_container = QWidget()
        content_container.setLayout(content_wrapper)
        root.addWidget(content_container, stretch=1)

        self._navigate("dashboard_btn")

    # ---------------------------------------------------------------- #
    #  Navigation                                                        #
    # ---------------------------------------------------------------- #

    _page_map = {
        "dashboard_btn": (0, "Dashboard"),
        "results_btn":   (1, "Results"),
        "logs_btn":      (2, "Event Logs"),
        "settings_btn":  (3, "Settings"),
        "export_btn":    (4, "Export"),
        "debug_btn":     (5, "Debugging Log"),
    }

    def _navigate(self, attr: str) -> None:
        idx, title = self._page_map[attr]
        self._stack.setCurrentIndex(idx)
        self._page_title.setText(title)
        for btn in self._nav_buttons:
            btn.setChecked(False)
        getattr(self, attr).setChecked(True)

        if idx == 1:
            self._results.refresh()
        elif idx == 2:
            self._logs.refresh()

    # ---------------------------------------------------------------- #
    #  Signal wiring                                                     #
    # ---------------------------------------------------------------- #

    def _connect_signals(self) -> None:
        # WebSocket server
        self._ws_server.server_started.connect(self._on_server_started)
        self._ws_server.server_stopped.connect(self._on_server_stopped)
        self._ws_server.client_connected.connect(self._on_esp_connected)
        self._ws_server.client_disconnected.connect(self._on_esp_disconnected)
        self._ws_server.vote_received.connect(self._on_vote)
        self._ws_server.error_received.connect(self._on_error)
        self._ws_server.hold_started.connect(self._dashboard.start_hold)
        self._ws_server.hold_cancelled.connect(self._dashboard.cancel_hold)

        # Logger → dashboard live events feed
        get_emitter().new_log.connect(self._dashboard.append_log)

        # Logger → debugging log page (all levels with colour)
        get_emitter().new_debug_log.connect(self._debug.append_entry)

        # Settings
        self._settings.names_changed.connect(self._on_names_changed)
        self._settings.session_cleared.connect(self._on_session_cleared)
        self._settings.fullscreen_requested.connect(self._on_fullscreen_requested)

    # ---------------------------------------------------------------- #
    #  WebSocket slots                                                   #
    # ---------------------------------------------------------------- #

    def _start_server(self) -> None:
        self._status_dot.set_starting()
        self._ws_server.start()

    @pyqtSlot(int)
    def _on_server_started(self, port: int) -> None:
        self._status_dot.set_online(port)
        log.info("WebSocket server ready on port %d", port)

    @pyqtSlot()
    def _on_server_stopped(self) -> None:
        self._status_dot.set_offline()

    @pyqtSlot(str)
    def _on_esp_connected(self, addr: str) -> None:
        self._status_dot.set_esp_connected(addr)
        log.info("ESP8266 connected from %s", addr)

    @pyqtSlot(str)
    def _on_esp_disconnected(self, addr: str) -> None:
        self._status_dot.set_esp_disconnected()
        log.warning("ESP8266 disconnected: %s", addr)

    @pyqtSlot(int)
    def _on_vote(self, candidate_id: int) -> None:
        name = self._candidate_map.get(candidate_id, f"Candidate {candidate_id}")
        record_vote(candidate_id, name, "vote")
        log.info("Vote Accepted → %s (ID %d)", name, candidate_id)
        # Flash the hold-progress bar to 100% then hide it
        self._dashboard.complete_hold()
        # Start the 10-second lockout countdown on the dashboard
        self._dashboard.start_lockout()
        # Immediate refresh — zero delay
        self._dashboard.refresh()

    @pyqtSlot(str)
    def _on_error(self, reason: str) -> None:
        record_vote(0, "N/A", f"error:{reason}")
        log.warning("Error → %s", reason)

    # ---------------------------------------------------------------- #
    #  Settings slots                                                    #
    # ---------------------------------------------------------------- #

    @pyqtSlot(dict)
    def _on_names_changed(self, candidate_map: dict) -> None:
        self._candidate_map = candidate_map
        self._dashboard.update_candidate_names(candidate_map)
        self._results.update_candidate_names(candidate_map)
        self._export.update_candidate_names(candidate_map)
        log.info("Candidate names updated")

    @pyqtSlot()
    def _on_session_cleared(self) -> None:
        self._dashboard.refresh()
        self._results.refresh()
        self._logs.refresh()
        log.info("Session cleared — new election started")

    @pyqtSlot(bool)
    def _on_fullscreen_requested(self, enter: bool) -> None:
        if enter:
            self.showFullScreen()
            log.info("Entered full screen mode")
        else:
            self.showNormal()
            log.info("Exited full screen mode")

    # ---------------------------------------------------------------- #
    #  Keyboard shortcuts                                                #
    # ---------------------------------------------------------------- #

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
        else:
            super().keyPressEvent(event)

    # ---------------------------------------------------------------- #
    #  Close                                                             #
    # ---------------------------------------------------------------- #

    def closeEvent(self, event) -> None:
        self._ws_server.stop()
        super().closeEvent(event)


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #

def _app_icon() -> QIcon:
    """
    Return a QIcon for the application window / taskbar.

    When frozen by PyInstaller, --add-data places icon.ico in sys._MEIPASS.
    When running as a plain script, look next to main.py.
    Falls back to an empty QIcon if the file is not found.
    """
    base = getattr(sys, "_MEIPASS", _HERE)
    path = os.path.join(base, "icon.ico")
    if os.path.isfile(path):
        return QIcon(path)
    return QIcon()


def main() -> None:
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    icon = _app_icon()
    app.setWindowIcon(icon)          # taskbar + any dialog that inherits it

    window = MainWindow()
    window.setWindowIcon(icon)       # title-bar corner icon
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
