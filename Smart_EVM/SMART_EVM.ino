/*
 * ============================================================
 *  SMART EVM — ESP8266 Firmware  v1.4
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
 *  5. Hold any candidate button for 2 seconds to cast a vote
 *     Two-beep confirmation + LED flash on confirmed vote
 *     10-second lockout prevents double-votes
 *     False vote attempt → 3-second continuous alarm
 *
 *  WIRING
 *  ─────────────────────────────────────────────────────────
 *  Candidate 1 button : D1 (GPIO5)  → GND   (no resistor needed)
 *  Candidate 2 button : D2 (GPIO4)  → GND
 *  Candidate 3 button : D5 (GPIO14) → GND
 *  Candidate 4 button : D6 (GPIO12) → GND
 *  Candidate 5 button : D7 (GPIO13) → GND
 *  Blue LED (+)       : D4 (GPIO2)  → 220Ω → GND (HIGH=ON)
 *  Active buzzer (+)  : D8 (GPIO15) → GND  (buzzer − to GND)
 *
 *  BUZZER NOTE
 *  ─────────────────────────────────────────────────────────
 *  GPIO15 (D8) has an onboard 10 kΩ pull-down resistor.
 *  For best results wire an NPN transistor (e.g. 2N2222):
 *    ESP D8 → 1 kΩ → Base
 *    Collector → Buzzer(+) → 3.3 V
 *    Emitter → GND
 *  Direct wiring also works for most active buzzers — if the
 *  buzzer is silent, swap its + and − legs (some modules have
 *  reversed markings).
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

const unsigned long VOTE_LOCKOUT_MS     = 10000; // 10-second lockout after confirmed vote
const unsigned long HOLD_REQUIRED_MS    = 2000;  // must hold 2 s to confirm vote
const unsigned long DEBOUNCE_MS         = 50;    // ms for button debounce
const unsigned long FALSE_VOTE_ALARM_MS = 3000;  // 3-second alarm for false vote / spam

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

// Non-blocking LED timer (0 = off/not scheduled)
uint32_t ledOffAt = 0;

// NEW: Non-blocking multi-beep sequencer
// Plays a sequence of (onMs, offMs) pairs without using delay().
struct BeepStep { uint16_t onMs; uint16_t offMs; };
static BeepStep beepQueue[8];
static int      beepQueueLen  = 0;
static int      beepQueueIdx  = 0;
static uint32_t beepStepEnd   = 0;
static bool     beepStepIsOn  = false;

// Slow status blink while disconnected
uint32_t statusBlinkAt  = 0;
bool     statusLedState = false;

// NEW: Hold-to-vote logic
int      holdCandidate  = -1;   // 0-based index of button being held (-1 = none)
uint32_t holdStartedAt  = 0;
bool     holdFired      = false;

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

// NEW: Schedule a non-blocking beep sequence.
// Pass pairs: onMs, offMs, onMs, offMs ... (max 8 steps total pairs).
// For a continuous alarm pass one step with a large onMs and offMs=0.
void scheduleBeep(BeepStep* steps, int count) {
  memcpy(beepQueue, steps, count * sizeof(BeepStep));
  beepQueueLen = count;
  beepQueueIdx = 0;
  // Start immediately: turn buzzer ON for first step
  buzzerSet(true);
  beepStepIsOn = true;
  beepStepEnd  = millis() + steps[0].onMs;
}

// NEW: Tick the beep sequencer — call every loop iteration
void tickBeep(uint32_t now) {
  if (beepQueueLen == 0) return;
  if (now < beepStepEnd)  return;   // still in current phase

  if (beepStepIsOn) {
    // ON phase done — start OFF phase
    buzzerSet(false);
    beepStepIsOn = false;
    uint16_t offMs = beepQueue[beepQueueIdx].offMs;
    if (offMs == 0 || beepQueueIdx >= beepQueueLen - 1) {
      // No off-phase or last step — sequence complete
      beepQueueLen = 0;
      return;
    }
    beepStepEnd = now + offMs;
  } else {
    // OFF phase done — advance to next step
    beepQueueIdx++;
    if (beepQueueIdx >= beepQueueLen) {
      beepQueueLen = 0;   // sequence finished
      return;
    }
    buzzerSet(true);
    beepStepIsOn = true;
    beepStepEnd  = now + beepQueue[beepQueueIdx].onMs;
  }
}

// NEW: Stop any running beep sequence immediately
void cancelBeep() {
  beepQueueLen = 0;
  buzzerSet(false);
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

void sendHoldStart(int candidateId) {
  char buf[64];
  snprintf(buf, sizeof(buf),
           "{\"type\":\"hold_start\",\"candidate_id\":%d}", candidateId);
  ws.sendTXT(buf);
  Serial.print("[TX] "); Serial.println(buf);
}

void sendHoldCancel(int candidateId) {
  char buf[64];
  snprintf(buf, sizeof(buf),
           "{\"type\":\"hold_cancel\",\"candidate_id\":%d}", candidateId);
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
  Serial.println("\n=== SMART EVM — ESP8266 v1.4 ===");

  // ── Pins ──────────────────────────────────────────────────
  for (int i = 0; i < 5; i++) {
    pinMode(BTNS[i], INPUT_PULLUP);
  }
  pinMode(PIN_LED,    OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  ledSet(false);
  buzzerSet(false);

  // Power-on buzzer test — two 400 ms beeps confirm hardware is alive.
  // If you hear these but not vote beeps, the non-blocking timer works.
  // If you hear NEITHER, check wiring (try swapping buzzer +/−).
  beepSync(2, 400, 150);
  delay(300);

  // ── WiFi Access Point ─────────────────────────────────────
  WiFi.persistent(false);
  WiFi.mode(WIFI_OFF);
  delay(100);
  WiFi.mode(WIFI_AP);

  bool apOk = (strlen(AP_PASSWORD) >= 8)
              ? WiFi.softAP(AP_SSID, AP_PASSWORD)
              : WiFi.softAP(AP_SSID);

  if (!apOk) {
    Serial.println("[WiFi] ERROR: Could not start Access Point!");
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
  ws.setReconnectInterval(3000);
  ws.enableHeartbeat(15000, 3000, 2);

  Serial.printf("[WS] Connecting to ws://%s:%u/ ...\n", WS_HOST, WS_PORT);
  Serial.println("=================================\n");
}

// ============================================================
//  LOOP
// ============================================================

void loop() {
  uint32_t now = millis();

  ws.loop();

  // ── Beep sequencer tick ───────────────────────────────────
  tickBeep(now);

  // ── Non-blocking LED off ──────────────────────────────────
  if (ledOffAt && now >= ledOffAt) {
    ledSet(false);
    ledOffAt = 0;
  }

  // ── Status blink while disconnected (0.5 Hz slow blink) ──
  if (!wsConnected && !ledOffAt) {
    if (now - statusBlinkAt >= 500) {
      statusBlinkAt  = now;
      statusLedState = !statusLedState;
      ledSet(statusLedState);
    }
  }

  // ── 10-second lockout expiry ──────────────────────────────
  if (voteLocked && (now - lockoutStart >= VOTE_LOCKOUT_MS)) {
    voteLocked = false;
    Serial.println("[BTN] Ready — 10-second lockout cleared");
  }

  // ── Button debounce scan ──────────────────────────────────
  for (int i = 0; i < 5; i++) {
    bool raw = digitalRead(BTNS[i]);   // LOW = pressed (pull-up active)

    if (raw != btnRaw[i]) {
      btnRaw[i]       = raw;
      btnChangedAt[i] = now;
    }

    if ((now - btnChangedAt[i]) >= DEBOUNCE_MS && raw != btnStable[i]) {
      btnStable[i] = raw;

      // NEW: False vote detection — pressed during lockout
      if (raw == LOW && voteLocked) {
        int cid = i + 1;
        Serial.printf("[BTN] Candidate %d false vote during lockout!\n", cid);
        if (wsConnected) sendError("false_vote_during_lockout");

        // 3-second continuous alarm: one long ON step, no off phase
        cancelBeep();
        BeepStep alarm[] = { {3000, 0} };
        scheduleBeep(alarm, 1);
        ledSet(true);
        ledOffAt = now + 3000;
        // Do NOT restart lockout timer
      }

      // NEW: Hold start — falling edge outside lockout
      if (raw == LOW && !voteLocked) {
        if (holdCandidate == -1) {
          holdCandidate = i;
          holdStartedAt = now;
          holdFired     = false;
          Serial.printf("[BTN] Candidate %d hold started\n", i + 1);
          if (wsConnected) sendHoldStart(i + 1);
        }
      }

      // NEW: Hold cancel — rising edge (released early)
      if (raw == HIGH && !voteLocked) {
        if (holdCandidate == i) {
          if (!holdFired) {
            Serial.printf("[BTN] Candidate %d hold cancelled\n", i + 1);
            if (wsConnected) sendHoldCancel(i + 1);
          }
          holdCandidate = -1;
          holdFired     = false;
        }
      }
    }
  }

  // NEW: Hold-to-vote — fires when 2-second threshold is reached
  if (!voteLocked && holdCandidate != -1 && !holdFired) {
    if ((now - holdStartedAt) >= HOLD_REQUIRED_MS) {
      int cid   = holdCandidate + 1;
      holdFired = true;

      Serial.printf("[BTN] Candidate %d CONFIRMED (held 2 s)\n", cid);

      if (wsConnected) {
        sendVote(cid);

        // NEW: Two-beep confirmation pattern — 300 ms on, 100 ms off, 300 ms on
        cancelBeep();
        BeepStep confirm[] = { {300, 100}, {300, 0} };
        scheduleBeep(confirm, 2);

        ledSet(true);
        ledOffAt = now + 700;   // LED on for full duration of both beeps
      } else {
        Serial.println("[BTN] Not connected — vote discarded");
        beepSync(2, 60, 60);  // 2 short error beeps
      }

      voteLocked   = true;
      lockoutStart = now;
      holdCandidate = -1;
      holdFired     = false;
    }
  }
}
