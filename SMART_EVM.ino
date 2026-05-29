/*
 * ============================================================
 *  SMART EVM — ESP8266 Firmware  v1.1
 * ============================================================
 *
 *  HOW IT WORKS
 *  ─────────────────────────────────────────────────────────
 *  1. ESP8266 starts as a WiFi Access Point ("SMART_EVM")
 *  2. Connect your PC's WiFi to "SMART_EVM"
 *     Windows will assign itself the IP 192.168.4.2
 *  3. Launch the SMART EVM desktop app on the PC
 *     (WebSocket server starts automatically on port 8765)
 *  4. ESP8266 auto-connects — 3 beeps confirm it is live
 *  5. Press any candidate button to cast a vote
 *     Blue LED flashes + buzzer beeps to confirm each vote
 *     2-second lockout prevents accidental double-votes
 *
 *  WIRING
 *  ─────────────────────────────────────────────────────────
 *  Candidate 1 button : D1 (GPIO5)  → GND   (no resistor needed)
 *  Candidate 2 button : D2 (GPIO4)  → GND
 *  Candidate 3 button : D5 (GPIO14) → GND
 *  Candidate 4 button : D6 (GPIO12) → GND
 *  Candidate 5 button : D7 (GPIO13) → GND
 *  Blue LED (+)       : D4 (GPIO2)  → 220Ω → GND
 *  Active buzzer (+)  : D8 (GPIO15) → GND  (buzzer − to GND)
 *
 *  REQUIRED LIBRARY
 *  ─────────────────────────────────────────────────────────
 *  Arduino IDE → Library Manager → search "WebSockets"
 *  Install: "arduinoWebSockets" by Markus Sattler
 *
 *  ARDUINO IDE BOARD SETTINGS
 *  ─────────────────────────────────────────────────────────
 *  Board        : NodeMCU 1.0 (ESP-12E Module)
 *  Upload Speed : 115200
 *  CPU Frequency: 80 MHz
 *
 *  SERIAL MONITOR: 115200 baud — shows live status messages
 * ============================================================
 */

#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>

// ============================================================
//  CONFIGURATION — only edit this section
// ============================================================

const char*    AP_SSID     = "SMART_EVM";
const char*    AP_PASSWORD = "12345678";   // min 8 chars; "" = open network

const char*    WS_HOST = "192.168.4.2";   // PC's IP on this AP (always .2)
const uint16_t WS_PORT = 8765;            // must match SMART EVM app

const unsigned long VOTE_LOCKOUT_MS = 2000; // ms buttons locked after a vote
const unsigned long DEBOUNCE_MS     = 50;   // ms for button debounce
const unsigned long BEEP_MS         = 150;  // ms buzzer on per vote
const unsigned long BLINK_MS        = 300;  // ms LED on per vote

// ============================================================
//  PIN DEFINITIONS
// ============================================================

//                        D1    D2    D5    D6    D7
const int BTNS[5] = {     5,    4,   14,   12,   13 };

const int PIN_LED    = 2;   // D4 — external blue LED → 220Ω → GND (HIGH=ON)
const int PIN_BUZZER = 15;  // D8 — active buzzer+ (HIGH=ON, − to GND)

// ============================================================
//  STATE
// ============================================================

WebSocketsClient ws;
bool wsConnected = false;

// Per-button debounce
bool     btnRaw[5]       = { HIGH, HIGH, HIGH, HIGH, HIGH };
bool     btnStable[5]    = { HIGH, HIGH, HIGH, HIGH, HIGH };
uint32_t btnChangedAt[5] = { 0, 0, 0, 0, 0 };

// Vote lockout
bool     voteLocked   = false;
uint32_t lockoutStart = 0;

// Non-blocking LED / buzzer timers (0 = not scheduled)
uint32_t ledOffAt    = 0;
uint32_t buzzerOffAt = 0;

// Slow status blink while disconnected
uint32_t statusBlinkAt  = 0;
bool     statusLedState = false;

// ============================================================
//  HELPERS
// ============================================================

void ledSet(bool on)    { digitalWrite(PIN_LED,    on ? HIGH : LOW); }
void buzzerSet(bool on) { digitalWrite(PIN_BUZZER, on ? HIGH : LOW); }

// Blocking beep — only used in setup() for boot/connection tones
void beepSync(int count, int onMs, int offMs) {
  for (int i = 0; i < count; i++) {
    ledSet(true);  buzzerSet(true);  delay(onMs);
    ledSet(false); buzzerSet(false);
    if (i < count - 1) delay(offMs);
  }
}

void sendVote(int candidateId) {
  char buf[64];
  snprintf(buf, sizeof(buf),
           "{\"type\":\"vote\",\"candidate_id\":%d}", candidateId);
  ws.sendTXT(buf);
  Serial.print("[TX] "); Serial.println(buf);
}

void sendError(const char* reason) {
  char buf[96];
  snprintf(buf, sizeof(buf),
           "{\"type\":\"error\",\"reason\":\"%s\"}", reason);
  ws.sendTXT(buf);
  Serial.print("[TX] "); Serial.println(buf);
}

// ============================================================
//  WEBSOCKET EVENT HANDLER
// ============================================================

void wsEvent(WStype_t type, uint8_t* payload, size_t len) {
  switch (type) {

    case WStype_CONNECTED:
      wsConnected    = true;
      statusLedState = false;
      ledSet(false);  // stop status blink immediately
      Serial.printf("[WS] Connected to ws://%s:%u/\n", WS_HOST, WS_PORT);
      beepSync(3, 70, 70);  // 3 beeps = connected and ready
      break;

    case WStype_DISCONNECTED:
      wsConnected = false;
      Serial.println("[WS] Disconnected — retrying every 3 s...");
      break;

    case WStype_TEXT:
      // PC can optionally send messages; log them
      Serial.printf("[WS RX] %s\n", (char*)payload);
      break;

    case WStype_ERROR:
      Serial.println("[WS] Socket error");
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
  Serial.println("\n=== SMART EVM — ESP8266 v1.1 ===");

  // ── Pins ──────────────────────────────────────────────────
  for (int i = 0; i < 5; i++) {
    pinMode(BTNS[i], INPUT_PULLUP);
  }
  pinMode(PIN_LED,    OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  ledSet(false);
  buzzerSet(false);

  // Power-on tone — confirms the board is alive
  beepSync(1, 300, 0);
  delay(400);

  // ── WiFi Access Point ─────────────────────────────────────
  // IMPORTANT: disconnect/off first, THEN set AP mode.
  // Calling disconnect(true) after mode(WIFI_AP) would reset
  // the mode back to WIFI_OFF — bug in some ESP8266 core builds.
  WiFi.persistent(false);   // never write config to flash
  WiFi.mode(WIFI_OFF);      // clean slate
  delay(100);
  WiFi.mode(WIFI_AP);       // now set Access Point mode

  bool apOk = (strlen(AP_PASSWORD) >= 8)
              ? WiFi.softAP(AP_SSID, AP_PASSWORD)
              : WiFi.softAP(AP_SSID);

  if (!apOk) {
    Serial.println("[WiFi] ERROR: Could not start Access Point!");
    // Rapid error beep loop — board needs a reboot
    while (true) { beepSync(1, 100, 100); }
  }

  Serial.println("[WiFi] Access Point started");
  Serial.print("[WiFi] SSID     : "); Serial.println(AP_SSID);
  Serial.print("[WiFi] Password : "); Serial.println(AP_PASSWORD);
  Serial.print("[WiFi] AP IP    : "); Serial.println(WiFi.softAPIP());
  Serial.println("[WiFi] → Connect your PC WiFi to this network");
  Serial.println("[WiFi] → Then launch SMART EVM on the PC");

  // ── WebSocket client ──────────────────────────────────────
  ws.begin(WS_HOST, WS_PORT, "/");
  ws.onEvent(wsEvent);
  ws.setReconnectInterval(3000);       // retry connection every 3 s
  ws.enableHeartbeat(15000, 3000, 2);  // ping every 15 s, timeout 3 s

  Serial.printf("[WS] Connecting to ws://%s:%u/ ...\n", WS_HOST, WS_PORT);
  Serial.println("=================================\n");
}

// ============================================================
//  LOOP
// ============================================================

void loop() {
  uint32_t now = millis();

  // Must be called every loop — drives reconnect, ping, receive
  ws.loop();

  // ── Non-blocking LED off ──────────────────────────────────
  if (ledOffAt && now >= ledOffAt) {
    ledSet(false);
    ledOffAt = 0;
  }

  // ── Non-blocking buzzer off ───────────────────────────────
  if (buzzerOffAt && now >= buzzerOffAt) {
    buzzerSet(false);
    buzzerOffAt = 0;
  }

  // ── Status blink while disconnected (0.5 Hz slow blink) ──
  if (!wsConnected && !ledOffAt) {
    if (now - statusBlinkAt >= 500) {
      statusBlinkAt  = now;
      statusLedState = !statusLedState;
      ledSet(statusLedState);
    }
  }

  // ── Vote lockout expiry ───────────────────────────────────
  if (voteLocked && (now - lockoutStart >= VOTE_LOCKOUT_MS)) {
    voteLocked = false;
    Serial.println("[BTN] Ready — lockout cleared");
  }

  // ── Button scan (paused during lockout) ──────────────────
  if (!voteLocked) {
    for (int i = 0; i < 5; i++) {
      bool raw = digitalRead(BTNS[i]);  // LOW = pressed (pull-up active)

      // Reset debounce timer whenever the raw reading changes
      if (raw != btnRaw[i]) {
        btnRaw[i]       = raw;
        btnChangedAt[i] = now;
      }

      // Only update stable state after DEBOUNCE_MS of no change
      if ((now - btnChangedAt[i]) >= DEBOUNCE_MS && raw != btnStable[i]) {
        btnStable[i] = raw;

        // Falling edge (HIGH→LOW) = button pressed
        if (raw == LOW) {
          int cid = i + 1;
          Serial.printf("[BTN] Candidate %d pressed\n", cid);

          if (wsConnected) {
            sendVote(cid);
            // Non-blocking vote feedback
            ledSet(true);    buzzerSet(true);
            ledOffAt    = now + BLINK_MS;
            buzzerOffAt = now + BEEP_MS;
          } else {
            Serial.println("[BTN] Not connected — vote discarded");
            beepSync(2, 60, 60);  // 2 short error beeps
          }

          voteLocked   = true;
          lockoutStart = now;
          break;  // handle only one button per loop pass
        }
      }
    }
  }
}
