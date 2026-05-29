# ⚡ SMART EVM — Smart Electronic Voting Machine

> Made by **Ayush Raj, 8-ICSE**

A complete electronic voting system built with an **ESP8266 microcontroller** and a **Windows desktop application**. Voters press and hold a push button for 5 seconds to cast their vote. The desktop app receives every vote instantly over Wi-Fi, counts it, updates live charts, and can export results to Excel.

---

## ✅ ESP8266 Code Compatibility

**The firmware in this repo is 100% compatible with the desktop app.**

| What the ESP8266 sends | What the app expects | Status |
|---|---|---|
| `{"type":"vote","candidate_id":3}` | Exactly this format | ✅ |
| `{"type":"error","reason":"locked"}` | Exactly this format | ✅ |
| `{"type":"error","reason":"cancelled"}` | Exactly this format | ✅ |
| Connects to **port 8765** | Server listens on **port 8765** | ✅ |
| Connects to IP **192.168.4.2** | PC gets this IP from ESP hotspot | ✅ |

> **How the IP works:** The ESP8266 creates a Wi-Fi hotspot and acts as a router at `192.168.4.1`. When your PC connects to that hotspot, the ESP's built-in DHCP server automatically assigns the PC the IP `192.168.4.2`. The ESP then connects **to the PC** as a WebSocket client — the PC app is the server. No configuration needed.

---

## 📋 Table of Contents

1. [What You Need](#what-you-need)
2. [How the System Works](#how-the-system-works)
3. [Part 1 — Upload Firmware to ESP8266](#part-1--upload-firmware-to-esp8266)
4. [Part 2 — Install the Desktop App](#part-2--install-the-desktop-app)
5. [Part 3 — Run Your First Election](#part-3--run-your-first-election)
6. [App Pages — Full Guide](#app-pages--full-guide)
7. [Wiring Guide](#wiring-guide)
8. [Troubleshooting](#troubleshooting)
9. [Project File Structure](#project-file-structure)

---

## What You Need

### Hardware
- NodeMCU ESP8266 board
- 5 × Push buttons (momentary, normally open)
- 1 × Blue LED + 220Ω resistor
- 1 × Active buzzer
- Jumper wires, breadboard, USB-A to Micro-USB cable

### Software (Windows PC)
- **Python 3.11 or newer** — [python.org/downloads](https://www.python.org/downloads/)
  > ⚠️ During installation, **check "Add Python to PATH"** before clicking Install
- **Arduino IDE 2.x** — [arduino.cc/en/software](https://www.arduino.cc/en/software)

---

## How the System Works

```
  Voter presses and holds push button (5 seconds)
               │
               ▼
     ESP8266 confirms continuous press
     Blue LED turns ON during countdown
               │
               ▼
     Sends vote packet over Wi-Fi ────────────► Desktop App on PC
               │                                       │
               ▼                                       ▼
     Buzzer beeps twice                    Saves vote to database
     10-second lockout starts              Updates live charts instantly
                                           Shows in event log
```

**Who does what:**
- The **ESP8266** handles only the physical side: buttons, blue LED, and buzzer
- The **PC app** handles everything else: counting, storing, charts, results, Excel export
- They talk over **Wi-Fi** using WebSocket — no internet needed, it's a direct link

---

## Part 1 — Upload Firmware to ESP8266

### Step 1 — Install Arduino IDE

Download and install from [arduino.cc/en/software](https://www.arduino.cc/en/software). Default settings are fine.

### Step 2 — Add ESP8266 board support

1. Open Arduino IDE → **File → Preferences**
2. Paste this into **"Additional boards manager URLs"**:
   ```
   https://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
3. Click **OK** → **Tools → Board → Boards Manager**
4. Search `esp8266` → Install **"ESP8266 by ESP8266 Community"**

### Step 3 — Install required libraries

Go to **Tools → Manage Libraries** and install each of these:

| Search for | Install this |
|---|---|
| `WebSockets` | **WebSockets** by Markus Sattler |
| `ArduinoJson` | **ArduinoJson** by Benoit Blanchon |

> `ESP8266WiFi` is already included — you do not need to install it separately.

### Step 4 — Upload the sketch

1. Open `smart_evm_esp8266.ino` in Arduino IDE
2. Connect ESP8266 to PC via USB
3. **Tools → Board** → select **NodeMCU 1.0 (ESP-12E Module)**
4. **Tools → Port** → select the COM port (e.g. `COM3`)
5. Click the **Upload** button (→ arrow icon)
6. Wait for **"Done uploading"**

### Step 5 — Verify

Open **Tools → Serial Monitor**, set baud to **115200**. You should see:
```
SoftAP Started
ESP IP: 192.168.4.1
```
The blue LED should be OFF (system is idle, waiting for a button press).

---

## Part 2 — Install the Desktop App

### Step 1 — Download the files

1. Go to the GitHub repository page
2. Click the green **Code** button → **Download ZIP**
3. Right-click the downloaded ZIP → **Extract All**
4. You will get a folder called `smart_evm` — keep all files inside it together

---

### Step 2 — Run SETUP.bat

> This is the **only step you ever need to do manually**. Everything else is automatic.

1. Open the `smart_evm` folder
2. **Double-click `SETUP.bat`**

A blue terminal window will open and work through these steps automatically:

```
Step 1 — Checks if Python is installed on your PC
         If NOT found → downloads Python 3.11 from python.org and installs it silently
         (no pop-ups, no clicking through an installer)

Step 2 — Creates a self-contained environment (.venv folder)
         This keeps SMART EVM's packages separate from anything else on your PC

Step 3 — Installs all required packages:
         PyQt6        (the app window and UI)
         websockets   (receives votes from ESP8266)
         matplotlib   (live bar and pie charts)
         openpyxl     (Excel export)
```

When it finishes, you will see:

```
==========================================
  Setup complete!

  To launch the app:
    * Double-click  START.bat
    * Double-click  launch.vbs   (no CMD window)
    * Double-click  launch.pyw   (no CMD window)
==========================================
```

Press any key to close the setup window.

> **How long does it take?**
> About 1–3 minutes on first run depending on your internet speed.
> Every run after that is instant.

> **When to run SETUP.bat again:**
> Only if the app stops working, you see a "module not found" error, or you move the `smart_evm` folder to a different drive.

---

### Step 3 — Choose your launcher

You have four ways to open the app. Pick the one that suits you:

---

#### Option A — `launch.vbs` ✅ Recommended for daily use

Double-click **`launch.vbs`**

- Opens the app with **zero CMD / terminal windows**
- Completely silent — nothing appears except the app itself
- Works on all versions of Windows

---

#### Option B — `launch.pyw`

Double-click **`launch.pyw`**

- Also opens the app with **no CMD window**
- Uses Python's built-in silent mode (`pythonw.exe`)
- If nothing happens after double-clicking, right-click → **Open with → Python**

---

#### Option C — `START.bat`

Double-click **`START.bat`**

- A green terminal window appears briefly, shows a status message, then closes automatically once the app is open
- Good for the first launch or when you want to see if anything goes wrong during startup
- If the app fails to open, the window stays visible so you can read the error

```
==========================================
  SMART EVM  --  Electronic Voting Machine
==========================================

  Python 3.11.x found.
  Starting SMART EVM...
  (This window will close automatically once the app opens)
```

---

#### Option D — `launch.exe` (build it once, use forever)

This creates a proper Windows `.exe` file with no CMD window and no setup required each time.

**How to build it (do this once after running SETUP.bat):**

1. Double-click **`make_exe.bat`**
2. Wait 1–2 minutes while PyInstaller compiles the launcher
3. When done, `launch.exe` will appear in the `smart_evm` folder
4. Double-click `launch.exe` to start the app — no CMD window, no Python needed visible

```
==========================================
  launch.exe created successfully!
  Double-click launch.exe to start the app
  with no CMD window.
==========================================
```

---

### Launcher comparison at a glance

| File | CMD window? | Requires setup first? | Notes |
|---|---|---|---|
| `SETUP.bat` | Yes (blue) | — | Run once to install everything |
| `START.bat` | Brief (green) | No — auto-installs if needed | Good for troubleshooting |
| `launch.vbs` | **None** | Yes — run SETUP.bat first | Best for daily use |
| `launch.pyw` | **None** | Yes — run SETUP.bat first | Alternative silent launcher |
| `launch.exe` | **None** | Run `make_exe.bat` once | Standalone executable |

**The correct order on a new PC:**

```
1. Double-click SETUP.bat    ← once only
2. Double-click launch.vbs   ← every time you want to open the app
```

---

### About the Debugging Log page

When you use `launch.vbs`, `launch.pyw`, or `launch.exe`, no CMD window ever opens. Instead, everything the app is doing internally is shown inside the app itself on the **Debugging Log** page (click it in the left sidebar).

This page shows:

| Colour | Meaning |
|---|---|
| 🔵 Blue | Normal operation (INFO) |
| 🟠 Orange | Warnings — e.g. ESP disconnected |
| 🔴 Red | Errors — something went wrong |
| ⚫ Grey | Detailed debug messages |

If the app ever behaves unexpectedly, open **Debugging Log** — the answer will be there.

---

## Part 3 — Run Your First Election

### 1. Power on the ESP8266
Connect it to USB. Wait a few seconds for it to boot.

### 2. Connect PC to ESP8266 Wi-Fi
1. Click Wi-Fi icon in the Windows taskbar
2. Find **`SMART_EVM`** → click **Connect**
3. Password: **`12345678`**

> ⚠️ Windows shows "No internet" — this is normal. It is a direct local link.

### 3. Launch the app
Double-click **`launch.vbs`** (or `START.bat`).

### 4. Confirm connection
Top-right of the app will change from:
```
● Server starting...
```
to:
```
● ESP connected  192.168.4.2:XXXXX
```

### 5. Cast a vote
A voter presses and **holds** a button for **5 continuous seconds**:

| Hardware state | Meaning |
|---|---|
| Blue LED turns ON | Button press detected, countdown in progress |
| Buzzer beeps twice | Vote accepted and sent to PC |
| Blue LED OFF, 10s wait | Lockout period — machine won't accept another vote yet |
| Blue LED OFF, ready | Machine ready for next voter |

The vote appears on the Dashboard instantly.

### 6. End the session
- Go to **Export** tab → save results to Excel
- To reset for a new election: **Settings → Clear All Data**

---

## App Pages — Full Guide

### 🏠 Dashboard

The main screen. Updates in real time every time a vote arrives.

<img src="assets/dashboard.jpg" alt="Dashboard" width="900">

- **5 vote counter cards** — one per candidate with live totals
- **Bar chart** — side-by-side comparison of all candidates
- **Pie chart** — percentage share of each candidate
- **Live Events feed** — every vote and error logged with timestamp as it happens
- **Total Votes** — running total in the top-right corner

---

### 📊 Results

Ranked table, sorted from highest to lowest votes.

<img src="assets/results.jpg" alt="Results" width="900">

- Each candidate shown with ID, name, votes, and percentage
- Coloured progress bar for each candidate
- Leading candidate highlighted with a green **LEADER** badge
- Click **Refresh** to manually reload

---

### 📋 Logs

Complete record of every event in the current session.

<img src="assets/logs.jpg" alt="Logs" width="900">

- Green **VOTE** badge for accepted votes
- Red badge for errors
- Exact timestamp for every entry
- Filter dropdown: All Events / Votes Only / Errors Only

| Error type | Meaning |
|---|---|
| `ERROR:LOCKED` | Button pressed during the 10-second lockout |
| `ERROR:CANCELLED` | Voter released the button before 5 seconds |

---

### ⚙️ Settings

Configure the system before an election.

<img src="assets/settings.jpg" alt="Settings" width="900">

**Candidate Names** — Give each button a real name. Button 1 could be "Rahul Sharma" instead of "Physics". Click **Save Names** after editing.

**Display** — Switch between full screen and windowed mode:
- Click **Enter Full Screen** to make the app fill the entire monitor
- Click **Exit Full Screen** to return to a normal window
- You can also press the **Esc** key to exit full screen at any time

**Network Configuration** — Shows connection details for reference.

**Clear All Data** — Deletes all votes and resets all counters. Use at the start of each new election.

---

### 📤 Export

Save results to an Excel file.

<img src="assets/export.jpg" alt="Export" width="900">

The Excel file contains:
- **Summary Sheet** — vote totals per candidate
- **Bar Chart** — automatically generated comparison chart
- **Pie Chart** — percentage distribution chart
- **Event Log Sheet** — every vote with its exact timestamp

How to export: Click **Browse…** to choose a save location → click **Export to Excel**.

---

### 🔧 Debugging Log

<img src="assets/dashboard.jpg" alt="Debugging Log" width="900">

This page shows everything the app is doing internally — what previously appeared in an external CMD / terminal window. No CMD window ever opens when you use `launch.vbs` or `launch.pyw`.

- **Blue entries** = INFO messages (normal operation)
- **Orange entries** = WARNINGS (e.g. ESP disconnected)
- **Red entries** = ERRORS (something went wrong)
- **Grey entries** = DEBUG messages

Use this page to diagnose any issues without opening a terminal.

---

## Wiring Guide

### Push Buttons → ESP8266

Each button connects between the ESP8266 pin and **GND**. The internal pull-up is used — no external resistors needed for the buttons.

| Button | ESP8266 Pin | Candidate slot |
|---|---|---|
| Button 1 | **D1** | Candidate 1 |
| Button 2 | **D2** | Candidate 2 |
| Button 3 | **D5** | Candidate 3 |
| Button 4 | **D6** | Candidate 4 |
| Button 5 | **D7** | Candidate 5 |

**Wiring each button:**
```
ESP8266 Pin (D1/D2/D5/D6/D7)  ──┤ Button ├──  GND
```

### Blue LED → ESP8266

The blue LED lights up during vote verification (when a button is being held).

| Component | ESP8266 Pin |
|---|---|
| Blue LED (+) via 220Ω resistor | **D4** |
| Blue LED (–) | GND |

```
D4  ──  [220Ω resistor]  ──  [LED +]  ──  [LED –]  ──  GND
```

### Buzzer → ESP8266

| Component | ESP8266 Pin |
|---|---|
| Buzzer (+) | **D8** |
| Buzzer (–) | GND |

### Full Wiring Summary

```
ESP8266 NodeMCU
│
├── D1  →  Button 1 → GND   (Candidate 1)
├── D2  →  Button 2 → GND   (Candidate 2)
├── D5  →  Button 3 → GND   (Candidate 3)
├── D6  →  Button 4 → GND   (Candidate 4)
├── D7  →  Button 5 → GND   (Candidate 5)
│
├── D4  →  220Ω → Blue LED (+) → Blue LED (–) → GND
├── D8  →  Buzzer (+)  |  Buzzer (–) → GND
│
├── 3.3V / GND  →  Common power rail
└── USB  →  PC for uploading firmware
```

> ⚠️ **Power tip:** Add a 470µF capacitor between 3.3V and GND near the ESP8266 to prevent resets when the Wi-Fi radio activates.

---

## Troubleshooting

### App never shows "ESP connected"
- Make sure PC Wi-Fi is connected to **SMART_EVM**
- Make sure ESP8266 is powered on
- If Windows Firewall shows a prompt → click **Allow access**
- Check the **Debugging Log** page in the app for error messages

### Votes not appearing on the dashboard
Open **Tools → Serial Monitor** (baud: 115200). When a button is held for 5 seconds you should see:
```
{"type":"vote","candidate_id":1}
```
If you see `WebSocket Disconnected`, run `ipconfig` in Command Prompt and check the IP of the SMART_EVM adapter. If it is not `192.168.4.2`, update this line in the firmware and re-upload:
```cpp
IPAddress serverIP(192, 168, 4, 2);
```

### Button triggers without being pressed / inverts
In the firmware, find:
```cpp
bool touched = digitalRead(TOUCH_PINS[i]);
```
Change to:
```cpp
bool touched = !digitalRead(TOUCH_PINS[i]);
```

### START.bat shows "Python not found"
Run **SETUP.bat** — it will detect that Python is missing and install it automatically.

### App closes immediately with an error
Open the **Debugging Log** page if the app opens at all. Otherwise, open Command Prompt, go to the `smart_evm` folder, and run `python main.py` to see the full error.

### How to build launch.exe
1. Run **SETUP.bat** first
2. Double-click **make_exe.bat**
3. `launch.exe` will appear in the `smart_evm` folder
4. Double-click it to start the app — no CMD window, no setup needed

---

## Project File Structure

```
smart_evm/
│
├── START.bat          ← Launch app (green CMD window, closes itself)
├── SETUP.bat          ← First-time setup / auto-installs Python
├── launch.vbs         ← Launch silently — no CMD window (recommended)
├── launch.pyw         ← Launch silently via pythonw — no CMD window
├── make_exe.bat       ← Builds launch.exe using PyInstaller (run once)
├── requirements.txt   ← Python package list
│
├── main.py            ← App entry point
├── websocket_server.py← Receives votes from ESP8266 in real time
├── database.py        ← Saves and reads votes (SQLite)
├── excel_export.py    ← Generates Excel report
├── charts.py          ← Live bar and pie chart widgets
├── config.py          ← All settings in one place
├── logger.py          ← Logging (output shown in Debugging Log page)
│
├── ui/
│   ├── dashboard.py   ← Dashboard page (live counters + charts)
│   ├── results_page.py← Ranked results table
│   ├── logs_page.py   ← Event log viewer
│   ├── settings_page.py← Settings + full screen controls
│   ├── export_page.py ← Excel export
│   └── debug_page.py  ← Debugging Log (replaces CMD window)
│
├── database/
│   └── evm.db         ← Vote database (auto-created)
├── exports/
│   └── results.xlsx   ← Default export location
└── assets/            ← Screenshots for this README
```

### Launcher comparison

| File | CMD window? | Needs setup first? | Has icon? |
|---|---|---|---|
| `START.bat` | Brief green window | No (auto-installs) | Windows batch icon |
| `launch.vbs` | **None** | Yes (run SETUP.bat) | Windows script icon |
| `launch.pyw` | **None** | Yes (run SETUP.bat) | Python icon |
| `launch.exe` | **None** | Run `make_exe.bat` once | Custom icon |

**Recommended workflow:**
1. Run `SETUP.bat` once on first use
2. Use `launch.vbs` or `launch.pyw` every day — no CMD window, no fuss
3. Optionally run `make_exe.bat` to get a proper `launch.exe`

---

## Tech Stack

| Component | Technology |
|---|---|
| Desktop GUI | Python 3.11 + PyQt6 |
| Real-time communication | WebSockets (asyncio) |
| Vote database | SQLite (built into Python) |
| Live charts | Matplotlib |
| Excel export | openpyxl |
| Microcontroller | ESP8266 NodeMCU |
| Input | Momentary push buttons |
| Feedback | Blue LED + active buzzer |
| Firmware language | C++ (Arduino framework) |

---

*Built as a complete IoT voting system for classroom and small-scale elections.*
*Made by **Ayush Raj, 8-ICSE***
