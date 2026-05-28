# SMART EVM — Desktop Application

A production-grade desktop Electronic Voting Machine application built with Python + PyQt6.

---

## Requirements

- **Python 3.11+**
- **Windows / macOS / Linux** (tested on Windows 10/11)
- The PC must connect to the ESP8266 Wi-Fi hotspot: **SMART_EVM** / password **12345678**

---

## Installation & Launch (Windows)

### First time setup
1. Install **Python 3.11+** from [python.org](https://www.python.org/downloads/)
   - During installation, **tick "Add Python to PATH"** before clicking Install
2. Unzip the project anywhere on your PC
3. Open the `smart_evm` folder
4. **Double-click `START.bat`** — it will automatically:
   - Create a virtual environment
   - Install all dependencies
   - Launch the app

From the second run onwards, just double-click **`START.bat`** — the app opens immediately.

> If you ever need to reinstall dependencies from scratch (e.g. after a Python upgrade), run **`SETUP.bat`** instead.

### Command line (advanced)
```bat
cd smart_evm
python main.py
```

---

## Project Structure

```
smart_evm/
├── main.py               # Entry point + main window
├── websocket_server.py   # Async WebSocket server (receives ESP packets)
├── database.py           # SQLite persistence layer
├── excel_export.py       # XLSX export using openpyxl
├── charts.py             # Matplotlib chart widgets
├── logger.py             # Centralised logging → Qt signals
├── config.py             # All configuration constants
│
├── ui/
│   ├── dashboard.py      # Live vote counters, charts, event feed
│   ├── results_page.py   # Sortable results table
│   ├── logs_page.py      # Full event log viewer with filtering
│   ├── settings_page.py  # Candidate name editor + session controls
│   └── export_page.py    # Excel export UI
│
├── database/
│   └── evm.db            # SQLite database (auto-created on first run)
│
├── exports/
│   └── results.xlsx      # Default export location
│
└── requirements.txt
```

---

## How It Works

### Network Setup

1. Power on the ESP8266 — it creates a Wi-Fi hotspot:
   - **SSID:** `SMART_EVM`
   - **Password:** `12345678`
2. Connect your PC to this hotspot.
3. Launch `python main.py` — the app starts a WebSocket server on port **8765**.
4. The ESP8266 connects to `ws://<PC-IP>:8765` and begins sending vote packets.

> **Finding your PC's IP on the ESP network:** usually `192.168.4.2`. Program this into the ESP8266 firmware as the WebSocket target address.

### WebSocket Protocol

**Vote packet** (sent by ESP after 5-second validated touch):
```json
{ "type": "vote", "candidate_id": 3 }
```

**Error packet** (sent on lockout or cancelled touch):
```json
{ "type": "error", "reason": "locked" }
```

The PC application is the sole authority for:
- Counting votes
- Mapping candidate IDs → names
- Database persistence
- Charts and analytics
- Excel export

The ESP handles only hardware: touch sensors, LCD, LEDs, buzzer, and WebSocket transmission.

---

## Features

| Feature | Details |
|---------|---------|
| **Dashboard** | Live vote counters per candidate, bar + pie charts, real-time event feed |
| **Results** | Sortable table with vote totals and percentage share |
| **Logs** | Filterable timestamped event history (votes + errors) |
| **Settings** | Edit candidate names (ID→name mapping), clear session data |
| **Export** | One-click `.xlsx` export with charts and full event log |

---

## Candidate Mapping

By default the 5 candidates are:

| ID | Name |
|----|------|
| 1 | Physics |
| 2 | Chemistry |
| 3 | Mathematics |
| 4 | Biology |
| 5 | English |

You can rename them any time from the **Settings** page — no restart needed.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `PyQt6` | GUI framework |
| `websockets` | Async WebSocket server |
| `openpyxl` | Excel export |
| `matplotlib` | Embedded charts |
| `qasync` | asyncio ↔ Qt event-loop bridge (included for future use) |
