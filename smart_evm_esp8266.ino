#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ====================================================
// WIFI
// ====================================================

const char* AP_SSID = "SMART_EVM";
const char* AP_PASSWORD = "12345678";

IPAddress serverIP(192, 168, 4, 2);
const uint16_t WS_PORT = 8765;

// ====================================================
// LCD (D1=SCL, D2=SDA)
// ====================================================

LiquidCrystal_I2C lcd(0x27, 16, 2);

// ====================================================
// WS
// ====================================================

WebSocketsClient webSocket;

// ====================================================
// PINS (FIXED STRUCTURE)
// ====================================================

// Candidates ONLY (NO boot conflict pins)
const uint8_t TOUCH_PINS[5] = { D3, D4, D5, D6, D7 };
const uint8_t CANDIDATE_IDS[5] = { 1, 2, 3, 4, 5 };

// LEDs on safe UART pins (careful but usable if debug disabled)
const uint8_t LED1 =  3;   // GPIO3
const uint8_t LED2 =  1;   // GPIO1
const uint8_t LED3 = D0;

// Buzzer
const uint8_t BUZZER_PIN = D8;

// ====================================================
// TIMING
// ====================================================

const unsigned long HOLD_TIME = 5000;
const unsigned long LOCKOUT_TIME = 10000;
const unsigned long DEBOUNCE_MS = 20;

// ====================================================
// STATE
// ====================================================

enum State { IDLE, VERIFY, LOCKOUT };
State state = IDLE;

// ====================================================
// VARIABLES
// ====================================================

int activeID = -1;
unsigned long pressStart = 0;
unsigned long lockStart = 0;
unsigned long lastLCD = 0;

bool lastStable[5] = {0};
bool lastRaw[5] = {0};
unsigned long lastChange[5] = {0};

// ====================================================
// DEBOUNCED READ (CRITICAL FIX)
// ====================================================

bool readStable(uint8_t pin, int i) {

  bool raw = digitalRead(pin);

  if (raw != lastRaw[i]) {
    lastChange[i] = millis();
    lastRaw[i] = raw;
  }

  if (millis() - lastChange[i] > DEBOUNCE_MS) {
    lastStable[i] = raw;
  }

  return lastStable[i];
}

// ====================================================
// SETUP
// ====================================================

void setup() {

  // IMPORTANT: prevent floating inputs
  for (int i = 0; i < 5; i++) {
    pinMode(TOUCH_PINS[i], INPUT_PULLUP);
  }

  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  Wire.begin(D2, D1);
  lcd.init();
  lcd.backlight();

  lcd.print("SMART EVM BOOT");

  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(AP_SSID, AP_PASSWORD);

  webSocket.begin(serverIP.toString(), WS_PORT, "/");
  webSocket.setReconnectInterval(5000);

  delay(800);

  state = IDLE;
}

// ====================================================
// LOOP
// ====================================================

void loop() {

  webSocket.loop();

  switch (state) {

    case IDLE:
      scanTouches();
      break;

    case VERIFY:
      verifyHold();
      break;

    case LOCKOUT:
      handleLockout();
      break;
  }

  updateLEDs();
}

// ====================================================
// TOUCH SCAN (FIXED EDGE TRIGGER)
// ====================================================

void scanTouches() {

  for (int i = 0; i < 5; i++) {

    bool pressed = !readStable(TOUCH_PINS[i], i); // ACTIVE LOW

    if (pressed && activeID == -1) {

      activeID = CANDIDATE_IDS[i];
      pressStart = millis();
      state = VERIFY;

      tone(BUZZER_PIN, 2000, 80);
      return;
    }
  }
}

// ====================================================
// VERIFY HOLD
// ====================================================

void verifyHold() {

  int index = activeID - 1;

  bool stillPressed = !digitalRead(TOUCH_PINS[index]);

  if (!stillPressed) {
    resetToIdle();
    return;
  }

  if (millis() - pressStart >= HOLD_TIME) {
    acceptVote();
  }
}

// ====================================================
// ACCEPT VOTE (NO SPAM FIX)
// ====================================================

void acceptVote() {

  StaticJsonDocument<128> doc;
  doc["type"] = "vote";
  doc["candidate_id"] = activeID;

  String out;
  serializeJson(doc, out);
  webSocket.sendTXT(out);

  tone(BUZZER_PIN, 2500, 120);

  lcd.clear();
  lcd.print("VOTE ACCEPTED");

  state = LOCKOUT;
  lockStart = millis();
}

// ====================================================
// LOCKOUT
// ====================================================

void handleLockout() {

  if (millis() - lockStart > LOCKOUT_TIME) {
    resetToIdle();
  }
}

// ====================================================
// RESET
// ====================================================

void resetToIdle() {

  activeID = -1;
  state = IDLE;
}

// ====================================================
// LEDS
// ====================================================

void updateLEDs() {

  digitalWrite(LED1, LOW);
  digitalWrite(LED2, LOW);
  digitalWrite(LED3, LOW);

  if (state == IDLE) digitalWrite(LED3, HIGH);
  if (state == VERIFY) digitalWrite(LED1, HIGH);
  if (state == LOCKOUT) digitalWrite(LED2, HIGH);
}
