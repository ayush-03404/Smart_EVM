# ⚡ SMART EVM — Smart Electronic Voting Machine

A complete electronic voting system built with an **ESP8266 microcontroller** and a **Windows desktop application**. Voters touch a sensor for 5 seconds to cast their vote. The desktop app receives the vote instantly, counts it, shows live charts, and can export results to Excel.

---

## ✅ ESP8266 Code Compatibility

**Your ESP8266 code is 100% compatible with this app.** Here is why:

| ESP8266 sends | App expects | Status |
|---|---|---|
| `{"type": "vote", "candidate_id": 3}` | Exactly this format | ✅ Match |
| `{"type": "error", "reason": "locked"}` | Exactly this format | ✅ Match |
| `{"type": "error", "reason": "cancelled"}` | Exactly this format | ✅ Match |
| Connects to port **8765** | Server listens on port **8765** | ✅ Match |
| Connects to IP **192.168.4.2** | PC gets this IP from ESP hotspot | ✅ Match |

> **Important:** When your PC connects to the ESP's Wi-Fi hotspot (`SMART_EVM`), Windows will automatically assign your PC the IP address `192.168.4.2`. The ESP firmware already points to this address, so no changes are needed.

---

## 📋 Table of Contents

1. [What You Need](#what-you-need)
2. [How the System Works](#how-the-system-works)
3. [Part 1 — Upload Code to ESP8266](#part-1--upload-code-to-esp8266)
4. [Part 2 — Install the Desktop App](#part-2--install-the-desktop-app)
5. [Part 3 — Connect Everything and Start Voting](#part-3--connect-everything-and-start-voting)
6. [App Guide — All Pages Explained](#app-guide--all-pages-explained)
7. [Wiring Guide](#wiring-guide)
8. [Troubleshooting](#troubleshooting)

---

## What You Need

### Hardware
- NodeMCU ESP8266 board
- 5× TTP223 touch sensor modules
- 1× I2C LCD display (16×2, address 0x27)
- 1× Green LED
- 1× Red LED
- 1× Blue LED
- 1× Active buzzer
- Jumper wires, breadboard, USB cable

### Software (on your PC)
- Windows 10 or 11
- Python 3.11 or newer — download from [python.org](https://www.python.org/downloads/)
  > ⚠️ During Python installation, **tick the checkbox "Add Python to PATH"** before clicking Install
- Arduino IDE — download from [arduino.cc](https://www.arduino.cc/en/software)

---

## How the System Works

```
  [Voter touches sensor]
          │
          ▼
  [ESP8266 waits 5 seconds]   ← validates the touch is real
          │
          ▼
  [ESP8266 sends vote packet] ─── Wi-Fi ──► [PC Desktop App]
          │                                        │
          ▼                                        ▼
  [LCD shows "VOTE ACCEPTED"]           [Counts vote in database]
  [10 second lockout begins]            [Updates charts live]
```

- The **ESP8266** only handles the physical hardware (sensors, LCD, LEDs, buzzer)
- The **PC app** handles everything else: counting votes, storing data, charts, export
- They communicate over **Wi-Fi** using a technology called WebSocket

---

## Part 1 — Upload Code to ESP8266

### Step 1 — Install Arduino IDE

1. Download Arduino IDE from [arduino.cc/en/software](https://www.arduino.cc/en/software)
2. Install it (just click Next through the installer)

### Step 2 — Add ESP8266 support to Arduino IDE

1. Open Arduino IDE
2. Click **File → Preferences**
3. In the box labelled *"Additional boards manager URLs"*, paste this URL:
   ```
   https://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
4. Click **OK**
5. Click **Tools → Board → Boards Manager**
6. Search for `esp8266`
7. Click **Install** next to *"ESP8266 by ESP8266 Community"*
8. Wait for it to finish, then close

### Step 3 — Install required libraries

In Arduino IDE, click **Tools → Manage Libraries**, then search and install each of these:

| Library name to search | Install this one |
|---|---|
| `WebSockets` | **WebSockets** by Markus Sattler |
| `ArduinoJson` | **ArduinoJson** by Benoit Blanchon |
| `LiquidCrystal I2C` | **LiquidCrystal I2C** by Frank de Brabander |

> `ESP8266WiFi` comes pre-installed with the ESP8266 board package — no need to install it separately.

### Step 4 — Open and upload the sketch

1. Open Arduino IDE
2. Click **File → Open** and select `smart_evm_esp8266.ino`
3. Connect your ESP8266 to your PC with a USB cable
4. Click **Tools → Board** and select **NodeMCU 1.0 (ESP-12E Module)**
5. Click **Tools → Port** and select the COM port that appeared (e.g. `COM3`)
6. Click the **Upload** button (the right-arrow icon →)
7. Wait for "Done uploading" to appear at the bottom

### Step 5 — Verify it is working

1. Click **Tools → Serial Monitor**
2. Set the baud rate to **115200** (bottom-right dropdown)
3. You should see:
   ```
   SoftAP Started
   ESP IP: 192.168.4.1
   ```
4. The LCD should display `READY TO VOTE / Hold 5 Seconds`

---

## Part 2 — Install the Desktop App

### Step 1 — Download and extract

1. Download `smart_evm.tar.gz` from this repository
2. Extract it — you will get a folder called `smart_evm`

> On Windows, you can extract `.tar.gz` files with [7-Zip](https://www.7-zip.org/) (free) — right-click the file → 7-Zip → Extract Here

### Step 2 — Install Python (if not already installed)

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.11 or newer
3. Run the installer
4. **IMPORTANT:** On the first screen, tick the box **"Add Python to PATH"** before clicking Install

### Step 3 — Launch the app

1. Open the `smart_evm` folder
2. **Double-click `START.bat`**

The first time you run it, a black window will appear and automatically install the required software. This takes about 1–2 minutes. After that, it will open the app automatically.

From the second run onwards, the app opens immediately when you double-click `START.bat`.

---

## Part 3 — Connect Everything and Start Voting

Follow these steps **in order** every time you want to run an election:

### Step 1 — Power on the ESP8266
Connect it to USB power. Wait for the LCD to show `READY TO VOTE`.

### Step 2 — Connect your PC to the ESP8266 Wi-Fi
1. On your PC, click the Wi-Fi icon in the taskbar
2. Find the network called **`SMART_EVM`**
3. Click **Connect**
4. Enter password: **`12345678`**
5. Click **Connect**

> ⚠️ Your PC will show "No internet" — this is normal. The ESP8266 only provides a local connection, not internet access.

### Step 3 — Launch the app
Double-click **`START.bat`** inside the `smart_evm` folder.

### Step 4 — Watch the connection indicator
In the top-right corner of the app, you will see a green dot appear:

```
● ESP connected  192.168.4.2:60412
```

This confirms the ESP8266 and the app are talking to each other. You are ready to vote!

### Step 5 — Cast a vote
A voter holds their finger on one of the 5 touch sensors for **5 continuous seconds**:
- The LCD shows a countdown (e.g. `VERIFYING / 3.2/5.0s`)
- The blue LED turns on during verification
- At 5 seconds, the buzzer beeps twice and the LCD shows `VOTE ACCEPTED`
- The green LED turns on again after the 10-second lockout

The vote appears instantly on the PC dashboard.

---

## App Guide — All Pages Explained

### 🏠 Dashboard

The main screen you see when the app opens. Everything updates in real time as votes come in.

![Dashboard](assets/dashboard.jpg)

**What you see:**
- **5 vote counter cards** — one for each candidate, showing their current total
- **Bar chart** — visual comparison of votes side by side
- **Pie chart** — percentage share of each candidate
- **Live Events feed** — every vote and error logged in real time with a timestamp
- **Total Votes counter** — top-right corner shows the running total

---

### 📊 Results

A clean table showing all candidates ranked by votes.

![Results](assets/results.jpg)

**What you see:**
- Each candidate listed with their ID, name, vote count, and share percentage
- A coloured progress bar showing each candidate's percentage
- The leading candidate is highlighted in green with a **LEADER** badge
- Click **Refresh** to manually update (the dashboard auto-updates every 5 seconds)

---

### 📋 Logs

A complete record of every single event, with exact timestamps.

![Logs](assets/logs.jpg)

**What you see:**
- Every accepted vote shown with a green **VOTE** badge
- Every error (locked, cancelled) shown with a red badge
- Exact date and time for each event
- Use the dropdown to filter: **All Events**, **Votes Only**, or **Errors Only**

**What the error types mean:**
- `ERROR:LOCKED` — Someone touched a sensor during the 10-second lockout period
- `ERROR:CANCELLED` — A voter lifted their finger before the 5 seconds were complete

---

### ⚙️ Settings

Configure the system before an election.

![Settings](assets/settings.jpg)

**What you can do:**

**Candidate Names** — Change the name shown for each button (1–5). The ESP8266 only knows the numbers; the app translates them to names. For example, Button 1 could be "John Smith" instead of "Physics". Click **Save Names** after editing.

**Network Configuration** — Shows the connection details for reference. You do not need to change these unless you modified the ESP8266 firmware.

**Clear All Data** — Deletes every vote record and starts fresh. Use this at the beginning of each new election. You will be asked to confirm before anything is deleted.

---

### 📤 Export

Save the results to an Excel file (.xlsx) for sharing or printing.

![Export](assets/export.jpg)

**What the Excel file contains:**
- **Summary Sheet** — vote totals for every candidate
- **Bar Chart** — automatically generated chart embedded in Excel
- **Pie Chart** — percentage distribution chart
- **Event Log Sheet** — every vote with its exact timestamp

**How to export:**
1. Click **Export** in the sidebar
2. The file path shows where the file will be saved (default: `exports/results.xlsx` inside the app folder)
3. Click **Browse…** to choose a different save location
4. Click the green **Export to Excel** button
5. A message will confirm when the file is saved

---

## Wiring Guide

### Touch Sensors → ESP8266

| Touch Sensor | ESP8266 Pin | Candidate |
|---|---|---|
| Sensor 1 | D1 | Button 1 (Physics) |
| Sensor 2 | D2 | Button 2 (Chemistry) |
| Sensor 3 | D5 | Button 3 (Mathematics) |
| Sensor 4 | D6 | Button 4 (Biology) |
| Sensor 5 | D7 | Button 5 (English) |

All TTP223 sensors: VCC → 3.3V, GND → GND, OUT → the pin above

### LEDs → ESP8266

| LED | ESP8266 Pin | Meaning |
|---|---|---|
| Green LED | D0 | Ready to vote (IDLE) |
| Red LED | D3 | Locked out (10s wait) |
| Blue LED | D4 | Touch being verified |

### Other Components

| Component | Connection |
|---|---|
| I2C LCD (SDA) | D2 (GPIO 4) |
| I2C LCD (SCL) | D1 (GPIO 5) |
| Buzzer | D8 |
| LCD VCC | 5V |
| LCD GND | GND |

> ⚠️ **Power tip:** Add a 470µF capacitor between 5V and GND close to the ESP8266 to prevent voltage drops when the Wi-Fi radio activates.

---

## Troubleshooting

### The app opens but stays "Server starting…" and never connects

- Make sure your PC is connected to the **SMART_EVM** Wi-Fi network
- Make sure the ESP8266 is powered on and its LCD shows `READY TO VOTE`
- Check that Windows Firewall is not blocking Python — if prompted, click **Allow**

### The ESP connects but votes don't appear

- Open the Arduino Serial Monitor and check the ESP is printing vote packets like:
  ```
  {"type":"vote","candidate_id":3}
  ```
- If it shows `WebSocket Disconnected`, the PC IP may be different from `192.168.4.2`. Check your IP: open Command Prompt → type `ipconfig` → look for the IP under the `SMART_EVM` adapter. If it is different (e.g. `192.168.4.3`), update `serverIP` in the `.ino` file and re-upload.

### The touch sensor triggers immediately without touching

- Your TTP223 module may have inverted logic. In the firmware, change:
  ```cpp
  bool touched = digitalRead(TOUCH_PINS[i]);
  ```
  to:
  ```cpp
  bool touched = !digitalRead(TOUCH_PINS[i]);
  ```

### `START.bat` shows "Python not found"

- Python is not installed or was installed without "Add to PATH"
- Uninstall Python, then reinstall it from [python.org](https://www.python.org/downloads/) — on the first installer screen, tick **"Add Python to PATH"**

### The app closes immediately with an error

- Run `START.bat` and read the error message before the window closes
- Or open Command Prompt, navigate to the `smart_evm` folder, and run `py main.py` to see the full error

---

## Project Structure

```
smart_evm/
├── START.bat             ← Double-click this to launch on Windows
├── SETUP.bat             ← Run this to reinstall dependencies
├── main.py               ← Main application (single entry point)
├── websocket_server.py   ← Receives votes from ESP8266
├── database.py           ← Stores votes in SQLite
├── excel_export.py       ← Generates Excel reports
├── charts.py             ← Bar and pie chart widgets
├── config.py             ← All settings in one place
├── logger.py             ← Event logging system
├── requirements.txt      ← Python package list
│
├── ui/
│   ├── dashboard.py      ← Dashboard page
│   ├── results_page.py   ← Results table
│   ├── logs_page.py      ← Event log viewer
│   ├── settings_page.py  ← Candidate names + session control
│   └── export_page.py    ← Excel export UI
│
├── database/
│   └── evm.db            ← Vote database (auto-created)
├── exports/
│   └── results.xlsx      ← Default export location
└── assets/               ← Screenshots and images
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Desktop GUI | Python + PyQt6 |
| Real-time communication | WebSockets |
| Vote storage | SQLite |
| Charts | Matplotlib |
| Excel export | openpyxl |
| Hardware | ESP8266 NodeMCU |
| Sensors | TTP223 capacitive touch |
| Display | I2C LCD 16×2 |

---

*Built as a complete IoT voting system. The ESP8266 handles all hardware interactions; the PC application handles all data, logic, and presentation.*
