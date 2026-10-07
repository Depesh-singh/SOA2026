/*
 * =====================================================
 * VayuNetra — ESP32 Tilt / Pan Servo Receiver
 * =====================================================
 * Hardware: MG996R Servo on GPIO 18 (D18)
 * Baud Rate: 115200 Baud
 * 
 * Supports both ASCII and JSON protocols:
 *   - TILT:<angle>
 *   - PAN:<angle>
 *   - {"pan": <angle>}
 * 
 * Direct Precision PWM mapping (50 Hz, 16-bit LEDC):
 *   - 0.0°   → ~500 µs pulse
 *   - 90.0°  → ~1500 µs pulse (NEUTRAL / BRAKE STOP)
 *   - 180.0° → ~2500 µs pulse
 * =====================================================
 */

#include <Arduino.h>

// ── Pin & PWM Config ──
#define SERVO_PIN         18
#define HEARTBEAT_LED     2
#define SERIAL_BAUD       115200

#define PWM_FREQ          50       // 50 Hz = 20 ms period
#define PWM_RESOLUTION    16       // 16-bit: 0..65535
#define DUTY_MIN          1638     // ~500 µs  → 0°
#define DUTY_MAX          8192     // ~2500 µs → 180°
#define DUTY_CENTER       4915     // ~1500 µs → 90° (NEUTRAL BRAKE)

// ── Limits ──
#define MIN_ANGLE         0.0f
#define MAX_ANGLE         180.0f

// ── State ──
float targetAngle   = 90.0f;
float currentAngle  = 90.0f;
String rxBuffer     = "";
uint32_t lastLed    = 0;
bool ledOn          = false;

// ── PWM Helpers ──
uint32_t angleToDuty(float deg) {
    deg = constrain(deg, MIN_ANGLE, MAX_ANGLE);
    if (abs(deg - 90.0f) < 0.15f) return DUTY_CENTER;
    return (uint32_t)(DUTY_MIN + (deg / 180.0f) * (DUTY_MAX - DUTY_MIN));
}

void writeServo(float deg) {
    uint32_t duty = angleToDuty(deg);
    #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
        ledcWrite(SERVO_PIN, duty);
    #else
        ledcWrite(0, duty);
    #endif
}

// ── Command Parsing ──
void parseLine(const String& line) {
    float val = -1.0f;

    if (line.startsWith("TILT:")) {
        val = line.substring(5).toFloat();
    } else if (line.startsWith("PAN:")) {
        val = line.substring(4).toFloat();
    } else if (line.indexOf("\"pan\":") >= 0) {
        int idx = line.indexOf("\"pan\":") + 6;
        while (idx < line.length() && (line[idx] == ' ' || line[idx] == ':')) idx++;
        val = line.substring(idx).toFloat();
    }

    if (val >= 0.0f && val <= 180.0f) {
        targetAngle = constrain(val, MIN_ANGLE, MAX_ANGLE);
        currentAngle = targetAngle;
        writeServo(currentAngle);
        Serial.print("OK:");
        Serial.println(targetAngle, 1);
    }
}

// ── Setup ──
void setup() {
    Serial.begin(SERIAL_BAUD);
    pinMode(HEARTBEAT_LED, OUTPUT);
    digitalWrite(HEARTBEAT_LED, LOW);

    // Init LEDC PWM on GPIO 18
    #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
        ledcAttach(SERVO_PIN, PWM_FREQ, PWM_RESOLUTION);
    #else
        ledcSetup(0, PWM_FREQ, PWM_RESOLUTION);
        ledcAttachPin(SERVO_PIN, 0);
    #endif

    currentAngle = 90.0f;
    targetAngle  = 90.0f;
    writeServo(90.0f); // Brake stop on boot

    delay(250);
    Serial.println("READY:90.0");
}

// ── Loop ──
void loop() {
    // 1. Read serial stream
    while (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') {
            rxBuffer.trim();
            if (rxBuffer.length() > 0) {
                parseLine(rxBuffer);
            }
            rxBuffer = "";
        } else {
            rxBuffer += c;
        }
    }

    // 2. Heartbeat LED
    uint32_t now = millis();
    if (now - lastLed >= 500) {
        lastLed = now;
        ledOn = !ledOn;
        digitalWrite(HEARTBEAT_LED, ledOn ? HIGH : LOW);
    }
}
