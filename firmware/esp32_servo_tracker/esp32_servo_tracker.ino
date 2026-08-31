/*
 * =====================================================================================
 * ESP32 MG996R Servo Tracker Firmware
 * Direct Single-Axis / Pan Gimbal Actuation Controller for SMART-SHIELD Anti-Drone System
 * =====================================================================================
 * Pinout:
 * - Servo Signal (PWM): GPIO 18 (D18) (MG996R Servo, 50Hz PWM, 500-2500us)
 * - Heartbeat LED:      GPIO 2  (Built-in LED)
 * - Serial Link:        USB CDC / UART0 @ 115200 baud
 *
 * Communication:
 * - Input (JSON):  {"pan": 90.0} or {"pan": 105.3, "threat": "HIGH"}
 * - Output (JSON): {"servo_pan": 90.0, "status": "TRACKING", "millis": 12345}
 * - Startup:       {"status": "READY", "servo_pan": 90.0}
 * =====================================================================================
 */

#include <Arduino.h>

// ----------------- CONFIGURATION CONSTANTS -----------------
#define SERVO_PIN         18       // GPIO 18 (D18) for MG996R PWM signal
#define HEARTBEAT_LED_PIN 2        // GPIO 2 for built-in heartbeat LED
#define SERIAL_BAUD       115200   // USB Serial baud rate

// PWM Configuration (Universal ESP32 Core 2.x & 3.x compatible)
#define PWM_CHANNEL       0        // LEDC PWM Channel for Core 2.x
#define PWM_FREQ_HZ       50       // 50Hz standard servo frequency (20ms period)
#define PWM_RESOLUTION    16       // 16-bit resolution (0 - 65535 ticks)
#define DUTY_MIN_TICKS    1638     // 500us pulse at 50Hz (0 deg) -> 65536 * 0.5/20.0
#define DUTY_MAX_TICKS    8192     // 2500us pulse at 50Hz (180 deg) -> 65536 * 2.5/20.0

// Motion Smoothing & Timing Parameters
#define MAX_STEP_DEG      2.0f     // Max angle increment per 20ms cycle (~100 deg/s)
#define SERVO_INTERVAL_MS 20       // Servo position update interval (50Hz)
#define ACK_INTERVAL_MS   100      // Serial acknowledgment telemetry interval (10Hz)
#define LED_BLINK_MS      500      // Heartbeat LED toggle interval

// ----------------- SYSTEM STATE -----------------
float targetPanAngle  = 90.0f;     // Desired pan angle (0.0 - 180.0 deg)
float currentPanAngle = 90.0f;     // Current smoothed servo position

uint32_t lastServoUpdate = 0;
uint32_t lastAckTime     = 0;
uint32_t lastLedBlink    = 0;
bool ledState            = false;

String serialRxBuffer    = "";

// ----------------- HELPER FUNCTIONS -----------------

// Converts pan angle (0-180 deg) to 16-bit LEDC duty cycle
uint32_t angleToDuty(float angleDeg) {
  angleDeg = constrain(angleDeg, 0.0f, 180.0f);
  return (uint32_t)(DUTY_MIN_TICKS + (angleDeg / 180.0f) * (DUTY_MAX_TICKS - DUTY_MIN_TICKS));
}

// Writes duty cycle directly to GPIO (compatible with Core 2.x and Core 3.x)
void applyServoDuty(float angleDeg) {
  uint32_t duty = angleToDuty(angleDeg);
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
    ledcWrite(SERVO_PIN, duty);
  #else
    ledcWrite(PWM_CHANNEL, duty);
  #endif
}

// Lightweight manual JSON parser for {"pan": 90.0} without external libraries
void parseSerialCommand(const String& cmd) {
  int panKeyIdx = cmd.indexOf("\"pan\"");
  if (panKeyIdx == -1) {
    panKeyIdx = cmd.indexOf("pan");
  }

  if (panKeyIdx != -1) {
    int colonIdx = cmd.indexOf(':', panKeyIdx);
    if (colonIdx != -1) {
      float parsedAngle = cmd.substring(colonIdx + 1).toFloat();
      targetPanAngle = constrain(parsedAngle, 0.0f, 180.0f);
    }
  }
}

// ----------------- SETUP & LOOP -----------------

void setup() {
  Serial.begin(SERIAL_BAUD);
  pinMode(HEARTBEAT_LED_PIN, OUTPUT);
  digitalWrite(HEARTBEAT_LED_PIN, LOW);

  // Initialize ESP32 LEDC PWM on GPIO 18 (D18)
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
    ledcAttach(SERVO_PIN, PWM_FREQ_HZ, PWM_RESOLUTION);
  #else
    ledcSetup(PWM_CHANNEL, PWM_FREQ_HZ, PWM_RESOLUTION);
    ledcAttachPin(SERVO_PIN, PWM_CHANNEL);
  #endif

  // Center servo to 90 degrees on startup
  currentPanAngle = 90.0f;
  targetPanAngle = 90.0f;
  applyServoDuty(currentPanAngle);

  // Send startup handshake
  Serial.println("{\"status\": \"READY\", \"servo_pan\": 90.0}");
}

void loop() {
  uint32_t now = millis();

  // 1. Process incoming Serial JSON commands
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialRxBuffer.length() > 0) {
        serialRxBuffer.trim();
        parseSerialCommand(serialRxBuffer);
        serialRxBuffer = "";
      }
    } else {
      if (serialRxBuffer.length() < 128) {
        serialRxBuffer += c;
      }
    }
  }

  // 2. Smooth Servo Motion Update (every 20ms)
  if (now - lastServoUpdate >= SERVO_INTERVAL_MS) {
    lastServoUpdate = now;
    if (abs(targetPanAngle - currentPanAngle) > 0.05f) {
      float delta = targetPanAngle - currentPanAngle;
      if (delta > MAX_STEP_DEG) delta = MAX_STEP_DEG;
      else if (delta < -MAX_STEP_DEG) delta = -MAX_STEP_DEG;
      
      currentPanAngle += delta;
      applyServoDuty(currentPanAngle);
    }
  }

  // 3. Heartbeat LED Toggle (every 500ms)
  if (now - lastLedBlink >= LED_BLINK_MS) {
    lastLedBlink = now;
    ledState = !ledState;
    digitalWrite(HEARTBEAT_LED_PIN, ledState ? HIGH : LOW);
  }

  // 4. Send Periodic Acknowledgment / Telemetry (every 100ms)
  if (now - lastAckTime >= ACK_INTERVAL_MS) {
    lastAckTime = now;
    Serial.printf("{\"servo_pan\": %.1f, \"status\": \"TRACKING\", \"millis\": %lu}\n",
                  currentPanAngle, (unsigned long)now);
  }
}
