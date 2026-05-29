/*
 * ============================================================
 *  SMART EVM — ESP8266 Firmware  v1.0
 * ============================================================
 *
 *  HOW IT WORKS
 *  ─────────────────────────────────────────────────────────
 *  1. ESP8266 starts as a WiFi Access Point ("SMART_EVM")
 *  2. Connect your PC's WiFi to "SMART_EVM" (password below)
 *     Windows will assign itself the IP 192.168.4.2
 *  3. Launch the SMART EVM desktop app on the PC
 *     (WebSocket server starts automatically on port 8765)
 *  4. ESP8266 auto-connects to the WebSocket server
 *  5. Press any candidate button to cast a vote
 *     → Blue LED flashes + buzzer beeps to confirm
 *     → 2-second lockout prevents accidental double-votes
 *
 *  WIRING
 *  ─────────────────────────────────────────────────────────
 *  Button 1 (Candidate 1) : D1 (GPIO5)  → GND
 *  Button 2 (Candidate 2) : D2 (GPIO4)  → GND
 *  Button 3 (Candidate 3) : D5 (GPIO14) → GND
 *  Button 4 (Candidate 4) : D6 (GPIO12) → GND
 *  Button 5 (Candidate 5) : D7 (GPIO13) → GND
 *  Blue LED               : D4 (GPIO2)  → 220Ω → GND
 *  Active Buzzer (+)      : D8 (GPIO15) → GND (buzzer −)
 *
 *  All buttons use the internal pull-up resistor.
 *  No external resistors needed for buttons.
 *
 *  REQUIRED LIBRARY
 *  ─────────────────────────────────────────────────────────
 *  Install via Arduino IDE → Library Manager:
 *    "arduinoWebSockets" by Markus Sattler   (search: WebSockets)
 *
 *  ARDUINO IDE BOARD SETTINGS
 *  ─────────────────────────────────────────────────────────
 *  Board      : NodeMCU 1.0 (ESP-12E Module)
 *  Upload Spd : 115200
 *  CPU Freq   : 80 MHz
 *  Flash Size : 4MB (FS:2MB OTA:~1019KB)
 *
 *  SERIAL MONITOR
 *  ─────────────────────────────────────────────────────────
 *  Baud rate: 115200 — open it to see live status messages
 * ============================================================
 */

#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>

// ============================================================
//  USER CONFIGURATION — edit here only
// ============================================================

// WiFi network that the ESP8266 will broadcast
const char* AP_SSID     = "SMART_EVM";
const char* AP_PASSWORD = "12345678";  // min 8 chars; set "" for open

// PC's IP on the ESP8266 AP network (Windows always gets .2)
const char* WS_HOST = "192.168.4.2";
const uint16_t WS_PORT = 8765;

// How long buttons are locked after each vote (ms)
const unsigned long VOTE_LOCKOUT_MS = 2000;

// Button debounce window (ms)
const unsigned long DEBOUNCE_MS = 50;

// Buzzer beep length (ms)
const unsigned long BEEP_MS = 150;

// LED flash length on vote (ms)
const unsigned long BLINK_MS = 300;

// ============================================================
//  PIN MAP
// ============================================================

const int BTNS[5] = {
  5,   // D1 → Candidate 1
  4,   // D2 → Candidate 2
  14,  // D5 → Candidate 3
  12,  // D6 → Candidate 4
  13   // D7 → Candidate 5
};

const int LED    = 2;   // D4 — external blue LED via 220Ω (HIGH = ON)
const int BUZZER = 15;  // D8 — active buzzer (HIGH = ON)

// ============================================================
//  STATE
// ============================================================

WebSocketsClient ws;
bool wsConnected = false;

// Debounce — standard stable-state tracker per button
bool     btnLastRaw[5]    = { HIGH, HIGH, HIGH, HIGH, HIGH };
bool     btnStable[5]     = { HIGH, HIGH, HIGH, HIGH, HIGH };
uint32_t btnChangeAt[5]   = { 0 };

// Vote lockout
bool     voteLocked   = false;
uint32_t lockoutStart = 0;

// Non-blocking LED & buzzer timers
uint32_t ledOffAt    = 0;
uint32_t buzzerOffAt = 0;

// Status blink (slow 0.5 Hz when disconnected)
uint32_t statusBlinkAt  = 0;
bool     statusLedState = false;

// ============================================================
//  LOW-LEVEL HELPERS
// ============================================================

void ledWrite(bool on) {
  digitalWrite(LED, on ? HIGH : LOW);
}

void buzzerWrite(bool on) {
  digitalWrite(BUZZER, on ? HIGH : LOW);
}

// Instant blocking beep — used only in setup for feedback
void beepBlocking(int times, int onMs, int offMs) {
  for (int i = 0; i < times; i++) {
    buzzerWrite(true);  ledWrite(true);
    delay(onMs);
    buzzerWrite(false); ledWrite(false);
    if (i < times - 1) delay(offMs);
  }
}

// ============================================================
//  WEBSOCKET
// ============================================================

void sendPacket(const char* json) {
  ws.sendTXT(json);
  Serial.print(F("[WS TX] "));
  Serial.println(json);
}

void sendVote(int candidateId) {
  char buf[64];
  snprintf(buf, sizeof(buf),
           "{\"type\":\"vote\",\"candidate_id\":%d}", candidateId);
  sendPacket(buf);
}

void sendError(const char* reason) {
  char buf[128];
  snprintf(buf, sizeof(buf),
           "{\"type\":\"error\",\"reason\":\"%s\"}", reason);
  sendPacket(buf);
}

void wsEventHandler(WStype_t type, uint8_t* payload, size_t len) {
  switch (type) {

    case WStype_CONNECTED:
      wsConnected = true;
      Serial.printf_P(PSTR("[WS] Connected → ws://%s:%u/\n"),
                      WS_HOST, WS_PORT);
      // 3 quick blinks to signal connection OK
      beepBlocking(3, 60, 60);
      break;

    case WStype_DISCONNECTED:
      wsConnected = false;
      Serial.println(F("[WS] Disconnected — will retry every 3 s"));
      break;

    case WStype_TEXT:
      // PC → ESP8266 messages (not expected, but log them)
      Serial.printf_P(PSTR("[WS RX] %s\n"), payload);
      break;

    case WStype_ERROR:
      Serial.println(F("[WS] Error event"));
      break;

    case WStype_PING:
      Serial.println(F("[WS] Ping received"));
      break;

    case WStype_PONG:
      Serial.println(F("[WS] Pong received"));
      break;

    default:
      break;
  }
}

// ============================================================
//  SETUP
// ============================================================

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println(F("\n\n=== SMART EVM — ESP8266 ==="));

  // ── Pin init ──────────────────────────────────────────────
  for (int i = 0; i < 5; i++) {
    pinMode(BTNS[i], INPUT_PULLUP);
  }
  pinMode(LED,    OUTPUT);
  pinMode(BUZZER, OUTPUT);
  ledWrite(false);
  buzzerWrite(false);

  // Startup blink — 1 long beep so user knows the board is alive
  beepBlocking(1, 200, 0);
  delay(300);

  // ── WiFi AP ───────────────────────────────────────────────
  WiFi.mode(WIFI_AP);
  WiFi.disconnect(true);
  delay(100);

  bool apOk;
  if (strlen(AP_PASSWORD) >= 8) {
    apOk = WiFi.softAP(AP_SSID, AP_PASSWORD);
  } else {
    apOk = WiFi.softAP(AP_SSID);
  }

  if (!apOk) {
    Serial.println(F("[WiFi] FAILED to start AP! Check board/power."));
    // Rapid error flicker forever
    while (true) {
      ledWrite(true);  buzzerWrite(true);  delay(100);
      ledWrite(false); buzzerWrite(false); delay(100);
    }
  }

  Serial.println(F("[WiFi] Access Point started"));
  Serial.print(F("[WiFi] SSID     : ")); Serial.println(AP_SSID);
  Serial.print(F("[WiFi] Password : ")); Serial.println(AP_PASSWORD);
  Serial.print(F("[WiFi] AP IP    : ")); Serial.println(WiFi.softAPIP());
  Serial.println(F("[WiFi] → Connect your PC to this WiFi network now."));
  Serial.println(F("[WiFi] → Then launch SMART EVM on the PC."));

  // ── WebSocket client ──────────────────────────────────────
  ws.begin(WS_HOST, WS_PORT, "/");
  ws.onEvent(wsEventHandler);
  ws.setReconnectInterval(3000);        // retry every 3 s if disconnected
  ws.enableHeartbeat(15000, 3000, 2);   // keepalive ping every 15 s

  Serial.printf_P(PSTR("[WS] Will connect to ws://%s:%u/\n"),
                  WS_HOST, WS_PORT);
  Serial.println(F("===========================\n"));
}

// ============================================================
//  LOOP
// ============================================================

void loop() {
  uint32_t now = millis();

  // ── WebSocket tick (must be called every loop) ────────────
  ws.loop();

  // ── Non-blocking LED off ──────────────────────────────────
  if (ledOffAt && now >= ledOffAt) {
    ledWrite(false);
    ledOffAt = 0;
  }

  // ── Non-blocking buzzer off ───────────────────────────────
  if (buzzerOffAt && now >= buzzerOffAt) {
    buzzerWrite(false);
    buzzerOffAt = 0;
  }

  // ── Status blink while disconnected ──────────────────────
  //    Slow 0.5 Hz blink (500 ms on, 500 ms off)
  //    Stops immediately when a vote feedback takes over
  if (!wsConnected && !ledOffAt) {
    if (now - statusBlinkAt >= 500) {
      statusBlinkAt = now;
      statusLedState = !statusLedState;
      ledWrite(statusLedState);
    }
  }

  // ── Vote lockout expiry ───────────────────────────────────
  if (voteLocked && (now - lockoutStart >= VOTE_LOCKOUT_MS)) {
    voteLocked = false;
    Serial.println(F("[BTN] Lockout lifted — ready for next vote"));
  }

  // ── Button scan (skipped during lockout) ─────────────────
  if (!voteLocked) {
    for (int i = 0; i < 5; i++) {
      bool raw = digitalRead(BTNS[i]);

      // Track raw signal changes for debounce timer
      if (raw != btnLastRaw[i]) {
        btnLastRaw[i]  = raw;
        btnChangeAt[i] = now;
      }

      // Accept new stable state only after DEBOUNCE_MS of silence
      if ((now - btnChangeAt[i]) >= DEBOUNCE_MS &&
          raw != btnStable[i]) {

        btnStable[i] = raw;

        // Falling edge = button pressed (HIGH → LOW with pullup)
        if (raw == LOW) {
          int cid = i + 1;
          Serial.printf_P(PSTR("[BTN] Candidate %d pressed\n"), cid);

          if (wsConnected) {
            sendVote(cid);

            // Vote feedback: LED + buzzer, non-blocking
            ledWrite(true);
            buzzerWrite(true);
            ledOffAt    = now + BLINK_MS;
            buzzerOffAt = now + BEEP_MS;

          } else {
            // Not connected — 2 error beeps, vote NOT sent
            Serial.println(F("[BTN] Not connected — vote discarded!"));
            beepBlocking(2, 60, 60);
          }

          // Lock buttons after every press (connected or not)
          voteLocked   = true;
          lockoutStart = now;
          break;  // only one vote per loop pass
        }
      }
    }
  }
}
