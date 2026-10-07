/*
 * =====================================================================================
 * ESP32 MG996R Smooth Drone Tracker Firmware
 * =====================================================================================
 * Wiring:
 * - Servo Signal Wire (Orange / Yellow) -> ESP32 GPIO 18 (D18)
 * - Servo Power (Red)                   -> External 5V / Battery (NOT ESP32 3.3V pin!)
 * - Servo Ground (Brown / Black)        -> Common Ground (ESP32 GND & Power GND)
 * =====================================================================================
 */

#include <Arduino.h>

// ----------------- CONFIGURATION SETTINGS -----------------
#define SERVO_PIN           18      // GPIO 18 (D18) for Servo Signal
#define HEARTBEAT_LED_PIN   2       // GPIO 2 for built-in LED
#define SERIAL_BAUD         115200  // USB Serial Baud Rate

// ----------------- STRICT SAFETY ANGLE LIMITS (22-30° RANGE) -----------------
#define SERVO_CENTER_DEG    90.0f   // Center neutral angle (Forward Boresight)
#define MAX_OFFSET_DEG      25.0f   // Maximum tilt offset from center
#define SERVO_MIN_DEG       (SERVO_CENTER_DEG - MAX_OFFSET_DEG)  // 65.0° (Hard Left Limit)
#define SERVO_MAX_DEG       (SERVO_CENTER_DEG + MAX_OFFSET_DEG)  // 115.0° (Hard Right Limit)

// ----------------- DIRECTION CONFIGURATION -----------------
// Set to false if: Drone on right -> Servo tilts right
// Set to true  if: Your servo mechanical mounting moves in the opposite direction
#define INVERT_DIRECTION    true

// ----------------- SPEED & SMOOTHING (ULTRA-SLOW CRAWL) -----------------
#define MAX_STEP_DEG        0.05f   // Ultra-slow speed: max 0.05° per 20ms = ~2.5°/second
#define DEADZONE_DEG        1.0f    // Deadband: holds motor completely still when centered
#define UPDATE_INTERVAL_MS  20      // 50Hz update loop (every 20ms)

// PWM Hardware Timer Configuration
#define PWM_CHANNEL         0
#define PWM_FREQ_HZ         50      // 50Hz servo refresh rate (20ms period)
#define PWM_RESOLUTION      16      // 16-bit timer (0-65535 ticks)
#define DUTY_MIN_TICKS      1638    // 500us pulse (0°)
#define DUTY_MAX_TICKS      8192    // 2500us pulse (180°)

// ----------------- STATE VARIABLES -----------------
float targetAngle   = SERVO_CENTER_DEG;
float currentAngle  = SERVO_CENTER_DEG;
uint32_t lastUpdate = 0;
uint32_t lastAck    = 0;
uint32_t lastBlink  = 0;
bool ledState       = false;
String rxBuffer     = "";

// ----------------- HELPER FUNCTIONS -----------------

// Strict clamp function: guarantees angle can NEVER exceed 65°-115° and NEVER exceeds 180°
float clampAngle(float angle) {
  if (isnan(angle) || isinf(angle)) return SERVO_CENTER_DEG;
  if (angle < SERVO_MIN_DEG) return SERVO_MIN_DEG;
  if (angle > SERVO_MAX_DEG) return SERVO_MAX_DEG;
  return angle;
}

// Convert angle (0-180°) to 16-bit PWM Duty Cycle ticks
uint32_t angleToDuty(float angle) {
  angle = clampAngle(angle);
  return (uint32_t)(DUTY_MIN_TICKS + (angle / 180.0f) * (DUTY_MAX_TICKS - DUTY_MIN_TICKS));
}

// Apply PWM pulse to GPIO pin
void applyServoDuty(float angle) {
  uint32_t duty = angleToDuty(angle);
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
    ledcWrite(SERVO_PIN, duty);
  #else
    ledcWrite(PWM_CHANNEL, duty);
  #endif
}

// Parse incoming JSON: {"pan": 90.0}
void parseCommand(const String& cmd) {
  int keyIdx = cmd.indexOf("\"pan\"");
  if (keyIdx == -1) keyIdx = cmd.indexOf("pan");

  if (keyIdx != -1) {
    int colonIdx = cmd.indexOf(':', keyIdx);
    if (colonIdx != -1) {
      float parsed = cmd.substring(colonIdx + 1).toFloat();
      
      #if INVERT_DIRECTION
        parsed = SERVO_CENTER_DEG - (parsed - SERVO_CENTER_DEG);
      #endif

      targetAngle = clampAngle(parsed);
    }
  }
}

// ----------------- SETUP & LOOP -----------------

void setup() {
  Serial.begin(SERIAL_BAUD);
  pinMode(HEARTBEAT_LED_PIN, OUTPUT);
  digitalWrite(HEARTBEAT_LED_PIN, LOW);

  // Initialize LEDC PWM
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
    ledcAttach(SERVO_PIN, PWM_FREQ_HZ, PWM_RESOLUTION);
  #else
    ledcSetup(PWM_CHANNEL, PWM_FREQ_HZ, PWM_RESOLUTION);
    ledcAttachPin(SERVO_PIN, PWM_CHANNEL);
  #endif

  // Start centered
  currentAngle = SERVO_CENTER_DEG;
  targetAngle  = SERVO_CENTER_DEG;
  applyServoDuty(currentAngle);

  // Quick 1-second physical startup verification (small gentle ±5° wiggle)
  delay(400);
  applyServoDuty(SERVO_CENTER_DEG + 6.0f);
  delay(300);
  applyServoDuty(SERVO_CENTER_DEG - 6.0f);
  delay(300);
  applyServoDuty(SERVO_CENTER_DEG);

  Serial.println("{\"status\": \"READY\", \"servo_pan\": 90.0, \"min\": 65.0, \"max\": 115.0}");
}

void loop() {
  uint32_t now = millis();

  // 1. Read Serial Command
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (rxBuffer.length() > 0) {
        rxBuffer.trim();
        parseCommand(rxBuffer);
        rxBuffer = "";
      }
    } else {
      if (rxBuffer.length() < 128) rxBuffer += c;
    }
  }

  // 2. Smooth Ultra-Slow Tracking Loop (every 20ms)
  if (now - lastUpdate >= UPDATE_INTERVAL_MS) {
    lastUpdate = now;
    
    targetAngle = clampAngle(targetAngle);
    float diff = targetAngle - currentAngle;

    // Deadband check: if within 1.0°, stay completely still (no jitter)
    if (abs(diff) > DEADZONE_DEG) {
      // Ultra-slow step (max 0.05° per step = ~2.5°/s)
      float step = constrain(diff * 0.08f, -MAX_STEP_DEG, MAX_STEP_DEG);
      currentAngle += step;
      currentAngle = clampAngle(currentAngle);
      applyServoDuty(currentAngle);
    }
  }

  // 3. Heartbeat LED (Blinks every 500ms to show ESP32 is running)
  if (now - lastBlink >= 500) {
    lastBlink = now;
    ledState = !ledState;
    digitalWrite(HEARTBEAT_LED_PIN, ledState ? HIGH : LOW);
  }

  // 4. Send Telemetry ACK every 100ms
  if (now - lastAck >= 100) {
    lastAck = now;
    Serial.printf("{\"servo_pan\": %.1f, \"status\": \"%s\"}\n",
                  currentAngle, (abs(targetAngle - currentAngle) <= DEADZONE_DEG) ? "HOLD_STEADY" : "FOLLOWING_SLOW");
  }
}
