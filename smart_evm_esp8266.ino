# FILE: smart_evm_esp8266.ino

```cpp
/*
====================================================
SMART EVM - ESP8266 Firmware
====================================================

ARCHITECTURE RULES:
- ESP handles ONLY:
    - touch sensing
    - 5s validation
    - 10s lockout
    - LCD feedback
    - LED feedback
    - buzzer feedback
    - WebSocket communication

- ESP DOES NOT:
    - store candidate names
    - count votes permanently
    - generate results
    - handle database
    - perform analytics

====================================================
*/

#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ====================================================
// WIFI CONFIGURATION
// ====================================================

const char* AP_SSID = "SMART_EVM";
const char* AP_PASSWORD = "12345678";

// PC APPLICATION IP
IPAddress serverIP(192, 168, 4, 2);

// WebSocket Port
const uint16_t WS_PORT = 8765;

// ====================================================
// LCD
// ====================================================

LiquidCrystal_I2C lcd(0x27, 16, 2);

// ====================================================
// WEBSOCKET
// ====================================================

WebSocketsClient webSocket;

// ====================================================
// GPIO DEFINITIONS
// ====================================================

// TTP223 INPUTS
const uint8_t TOUCH_PINS[5] = {
  D5,
  D6,
  D7,
   3,
   1,
};

// Candidate IDs
const uint8_t CANDIDATE_IDS[5] = {
  1,
  2,
  3,
  4,
  5
};

// LEDs
const uint8_t GREEN_LED = D0;
const uint8_t RED_LED   = D3;
const uint8_t BLUE_LED  = D4;

// Buzzer
const uint8_t BUZZER_PIN = D8;

// ====================================================
// TIMING
// ====================================================

const unsigned long TOUCH_DURATION = 5000;
const unsigned long LOCKOUT_DURATION = 10000;

// ====================================================
// SYSTEM STATES
// ====================================================

enum SystemState {
  IDLE,
  TOUCH_VERIFY,
  VOTE_ACCEPTED,
  LOCKOUT
};

SystemState currentState = IDLE;

// ====================================================
// TOUCH VARIABLES
// ====================================================

bool touchActive = false;
unsigned long touchStartTime = 0;
int activeCandidate = -1;

// ====================================================
// LOCKOUT VARIABLES
// ====================================================

bool locked = false;
unsigned long lockoutStartTime = 0;

// ====================================================
// TIMERS
// ====================================================

unsigned long lastLCDUpdate = 0;

// ====================================================
// FUNCTION DECLARATIONS
// ====================================================

void setupWiFi();
void setupWebSocket();

void handleTouchInputs();
void handleStateMachine();

void startTouchVerification(int candidateID);
void cancelTouch();
void acceptVote();

void startLockout();
void handleLockout();

void sendVotePacket(int candidateID);
void sendErrorPacket(const char* reason);

void updateLCD();
void updateLEDs();

void buzzerShort();
void buzzerDouble();
void buzzerLong();
void buzzerChirp();

void websocketEvent(WStype_t type, uint8_t * payload, size_t length);

// ====================================================
// SETUP
// ====================================================

void setup() {

  // INPUTS
  for (int i = 0; i < 5; i++) {
    pinMode(TOUCH_PINS[i], INPUT);
  }

  // OUTPUTS
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(BLUE_LED, OUTPUT);

  pinMode(BUZZER_PIN, OUTPUT);

  // LCD
  lcd.init();
  lcd.backlight();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SMART EVM");
  lcd.setCursor(0, 1);
  lcd.print("Booting...");

  // WiFi
  setupWiFi();

  // WebSocket
  setupWebSocket();

  delay(1000);

  currentState = IDLE;

  updateLCD();
}

// ====================================================
// MAIN LOOP
// ====================================================

void loop() {

  webSocket.loop();

  handleStateMachine();

  updateLEDs();
}

// ====================================================
// WIFI SETUP
// ====================================================

void setupWiFi() {

  WiFi.mode(WIFI_AP_STA);

  WiFi.softAP(AP_SSID, AP_PASSWORD);

  delay(500);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SoftAP Ready");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.softAPIP());
}

// ====================================================
// WEBSOCKET SETUP
// ====================================================

void setupWebSocket() {

  webSocket.begin(serverIP.toString(), WS_PORT, "/");

  webSocket.onEvent(websocketEvent);

  webSocket.setReconnectInterval(5000);
}

// ====================================================
// WEBSOCKET EVENTS
// ====================================================

void websocketEvent(WStype_t type, uint8_t * payload, size_t length) {

  switch(type) {

    case WStype_DISCONNECTED:
      Serial.println("WebSocket Disconnected");
      break;

    case WStype_CONNECTED:
      Serial.println("WebSocket Connected");
      break;

    case WStype_TEXT:
      Serial.printf("Received: %s\n", payload);
      break;

    default:
      break;
  }
}

// ====================================================
// STATE MACHINE
// ====================================================

void handleStateMachine() {

  switch(currentState) {

    case IDLE:
      handleTouchInputs();
      break;

    case TOUCH_VERIFY:

      if (activeCandidate == -1) {
        cancelTouch();
        return;
      }

      // Verify continuous touch
      if (digitalRead(TOUCH_PINS[activeCandidate - 1]) == LOW) {

        cancelTouch();
        return;
      }

      unsigned long elapsed =
        millis() - touchStartTime;

      if (elapsed >= TOUCH_DURATION) {

        acceptVote();
      }

      updateLCD();

      break;

    case VOTE_ACCEPTED:
      startLockout();
      break;

    case LOCKOUT:
      handleLockout();
      break;
  }
}

// ====================================================
// TOUCH INPUT HANDLING
// ====================================================

void handleTouchInputs() {

  for (int i = 0; i < 5; i++) {

    bool touched = digitalRead(TOUCH_PINS[i]);

    if (touched) {

      if (locked) {

        sendErrorPacket("locked");

        buzzerChirp();

        return;
      }

      startTouchVerification(CANDIDATE_IDS[i]);

      return;
    }
  }
}

// ====================================================
// START TOUCH VERIFICATION
// ====================================================

void startTouchVerification(int candidateID) {

  touchActive = true;

  activeCandidate = candidateID;

  touchStartTime = millis();

  currentState = TOUCH_VERIFY;

  buzzerShort();

  updateLCD();
}

// ====================================================
// CANCEL TOUCH
// ====================================================

void cancelTouch() {

  sendErrorPacket("cancelled");

  buzzerLong();

  touchActive = false;

  activeCandidate = -1;

  currentState = IDLE;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("TOUCH");
  lcd.setCursor(0, 1);
  lcd.print("CANCELLED");

  delay(1000);

  updateLCD();
}

// ====================================================
// ACCEPT VOTE
// ====================================================

void acceptVote() {

  sendVotePacket(activeCandidate);

  buzzerDouble();

  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("VOTE");

  lcd.setCursor(0, 1);
  lcd.print("ACCEPTED");

  currentState = VOTE_ACCEPTED;
}

// ====================================================
// START LOCKOUT
// ====================================================

void startLockout() {

  locked = true;

  lockoutStartTime = millis();

  currentState = LOCKOUT;
}

// ====================================================
// HANDLE LOCKOUT
// ====================================================

void handleLockout() {

  unsigned long elapsed =
    millis() - lockoutStartTime;

  unsigned long remaining =
    (LOCKOUT_DURATION - elapsed) / 1000;

  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("PLEASE WAIT");

  lcd.setCursor(0, 1);
  lcd.print(remaining);
  lcd.print(" Seconds");

  if (elapsed >= LOCKOUT_DURATION) {

    locked = false;

    touchActive = false;

    activeCandidate = -1;

    currentState = IDLE;

    updateLCD();
  }
}

// ====================================================
// SEND VOTE PACKET
// ====================================================

void sendVotePacket(int candidateID) {

  StaticJsonDocument<128> doc;

  doc["type"] = "vote";
  doc["candidate_id"] = candidateID;

  String jsonString;

  serializeJson(doc, jsonString);

  webSocket.sendTXT(jsonString);

}

// ====================================================
// SEND ERROR PACKET
// ====================================================

void sendErrorPacket(const char* reason) {

  StaticJsonDocument<128> doc;

  doc["type"] = "error";
  doc["reason"] = reason;

  String jsonString;

  serializeJson(doc, jsonString);

  webSocket.sendTXT(jsonString);

}

// ====================================================
// LCD UPDATE
// ====================================================

void updateLCD() {

  if (millis() - lastLCDUpdate < 200)
    return;

  lastLCDUpdate = millis();

  switch(currentState) {

    case IDLE:

      lcd.clear();

      lcd.setCursor(0, 0);
      lcd.print("READY TO VOTE");

      lcd.setCursor(0, 1);
      lcd.print("Hold 5 Seconds");

      break;

    case TOUCH_VERIFY: {

      unsigned long elapsed =
        millis() - touchStartTime;

      float seconds =
        elapsed / 1000.0;

      lcd.clear();

      lcd.setCursor(0, 0);
      lcd.print("VERIFYING");

      lcd.setCursor(0, 1);

      lcd.print(seconds, 1);
      lcd.print("/5.0s");

      break;
    }

    default:
      break;
  }
}

// ====================================================
// LED CONTROL
// ====================================================

void updateLEDs() {

  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  digitalWrite(BLUE_LED, LOW);

  switch(currentState) {

    case IDLE:
      digitalWrite(GREEN_LED, HIGH);
      break;

    case TOUCH_VERIFY:
      digitalWrite(BLUE_LED, HIGH);
      break;

    case LOCKOUT:
      digitalWrite(RED_LED, HIGH);
      break;

    default:
      break;
  }
}

// ====================================================
// BUZZER FUNCTIONS
// ====================================================

void buzzerShort() {

  tone(BUZZER_PIN, 2000, 100);
}

void buzzerDouble() {

  tone(BUZZER_PIN, 2500, 100);

  delay(150);

  tone(BUZZER_PIN, 2500, 100);
}

void buzzerLong() {

  tone(BUZZER_PIN, 1000, 500);
}

void buzzerChirp() {

  tone(BUZZER_PIN, 3000, 50);

  delay(70);

  tone(BUZZER_PIN, 3000, 50);
}
```

# REQUIRED LIBRARIES

Install these libraries in Arduino IDE:

```txt id="h7l0of"
ESP8266WiFi
WebSockets by Markus Sattler
ArduinoJson
LiquidCrystal_I2C
```

# IMPORTANT NOTES

## 1. PC IP ADDRESS

Your PC MUST connect to ESP8266 SoftAP.

Usually the PC gets:

```txt id="r4iyyz"
192.168.4.2
```

If different:

* change serverIP in firmware

---

## 2. WEBSOCKET SERVER

The PyQt6 application MUST run:

* WebSocket server
* port 8765

---

## 3. POWER WARNING

ESP8266 is extremely sensitive to voltage drops.

Add:

* 470µF capacitor near ESP8266
* stable 5V supply
* common ground

---

## 4. IMPORTANT BUG WARNING

This code uses:

```cpp id="7smv8j"
delay()
```

inside buzzer functions.

That is acceptable SHORT TERM.

Later you SHOULD replace with:

* millis()-based nonblocking buzzer system

for maximum responsiveness.

---

## 5. TTP223 SIGNAL LEVEL

Most TTP223 modules output:

```txt id="ux5mze"
HIGH when touched
LOW when released
```

If your module behaves opposite:
invert logic here:

```cpp id="1phcc3"
bool touched = digitalR
