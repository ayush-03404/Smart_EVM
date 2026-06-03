"""
config.py — Global application configuration constants.
"""

APP_NAME = "SMART EVM"
APP_VERSION = "1.0.0"

# WebSocket server settings (ESP8266 connects TO this PC server)
WS_HOST = "0.0.0.0"
WS_PORT = 8765

# SQLite database path
DB_PATH = "database/evm.db"

# Export path
EXPORT_PATH = "exports/results.xlsx"

# Default candidate names — editable from the Settings page
DEFAULT_CANDIDATES = {
    1: "Physics",
    2: "Chemistry",
    3: "Mathematics",
    4: "Biology",
    5: "English",
}

# Total number of candidates (fixed by hardware)
CANDIDATE_COUNT = 5

# Dark theme palette
COLORS = {
    "bg_primary":    "#0d1117",
    "bg_secondary":  "#161b22",
    "bg_card":       "#1c2128",
    "bg_sidebar":    "#010409",
    "accent":        "#58a6ff",
    "accent_green":  "#3fb950",
    "accent_red":    "#f85149",
    "accent_orange": "#d29922",
    "text_primary":  "#e6edf3",
    "text_muted":    "#8b949e",
    "border":        "#30363d",
}
