/*
 * VayuNetra — Slow, Controlled Dual-Axis (Pan & Tilt) Drone Tracker Driver
 * PCA9685: Channel 0 (Pan), Channel 1 (Tilt), Channel 2 (Alt Tilt)
 * ESP32 GPIO: GPIO 18 (Pan), GPIO 19 (Tilt)
 *
 * REQUIREMENTS IMPLEMENTED:
 * 1. Slow, smooth speed: 50 Hz slew rate interpolation (no sudden jerking).
 * 2. Moves ONLY when it sees the drone (tracking == true).
 * 3. When no drone is seen or stopped: PWM is cut to 0V (ZERO crawl, 100% dead stop).
 * 4. Tilt is strictly limited to 30° up and 30° down (60.0° to 120.0°).
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

#define CH_PAN            0
#define CH_TILT           1
#define CH_TILT_ALT       2

#define PCA_SERVOMIN      102   // ~500 µs (0°)
#define PCA_SERVOMAX      512   // ~2500 µs (180°)
#define PCA_SERVO_CENTER  307   // ~1500 µs (90° Neutral)

#define DIRECT_GPIO_PAN   18
#define DIRECT_GPIO_TILT  19
#define HEARTBEAT_LED     2
#define SERIAL_BAUD       115200

#define PWM_FREQ          50
#define PWM_RESOLUTION    16
#define GPIO_DUTY_MIN     1638
#define GPIO_DUTY_MAX     8192
#define GPIO_DUTY_CENTER  4915

#define MIN_ANGLE         0.0f
#define MAX_ANGLE         180.0f
#define INVERT_PAN        true
#define INVERT_TILT       false

// Strict physical limits for Vertical Tilt: 30° Up / 30° Down from 90° center
#define MIN_TILT_ANGLE    60.0f   // 90° - 30° = 60° (30° Up)
#define MAX_TILT_ANGLE    120.0f  // 90° + 30° = 120° (30° Down)

// Slow Slew Rate Limits (Degrees per 20ms update cycle)
#define MAX_PAN_STEP      0.15f   // ~7.5°/sec max pan speed (smooth, controlled)
#define MAX_TILT_STEP     0.10f   // ~5.0°/sec max tilt speed (smooth, gentle)

// Safety Watchdog: If no tracking command received for > 350ms, STOP ALL MOTORS!
#define SAFETY_WATCHDOG_MS 350

// ── Runtime State ──
float currentPan         = 90.0f;
float currentTilt        = 90.0f;
float targetPan          = 90.0f;
float targetTilt         = 90.0f;
bool isTracking          = false;
String rxBuffer          = "";
uint32_t lastCommandTime = 0;
uint32_t lastSlewUpdate  = 0;
uint32_t lastHeartbeat   = 0;
bool ledState            = false;

uint16_t angleToPcaPulse(float deg) {
    deg = constrain(deg, MIN_ANGLE, MAX_ANGLE);
    if (abs(deg - 90.0f) < 0.2f) return PCA_SERVO_CENTER;
    return (uint16_t)map((int)(deg * 10), 0, 1800, PCA_SERVOMIN, PCA_SERVOMAX);
}

uint32_t angleToGpioDuty(float deg) {
    deg = constrain(deg, MIN_ANGLE, MAX_ANGLE);
    if (abs(deg - 90.0f) < 0.2f) return GPIO_DUTY_CENTER;
    return (uint32_t)(GPIO_DUTY_MIN + (deg / 180.0f) * (GPIO_DUTY_MAX - GPIO_DUTY_MIN));
}

// ── HARDWARE OUTPUT APPLIER ──
void applyOutputs(float pan, float tilt, bool trackingActive) {
    if (!trackingActive) {
        // Drone NOT seen / system idle -> COMPLETE STOP!
        // Cut PWM to 0V on both channels: completely powers off motor drivers!
        // ZERO RPM, ZERO CRAWL, ZERO DRIFT!
        pwm.setPin(CH_PAN, 0, false);
        pwm.setPin(CH_TILT, 0, false);
        pwm.setPin(CH_TILT_ALT, 0, false);
        #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
            ledcWrite(DIRECT_GPIO_PAN, 0);
            ledcWrite(DIRECT_GPIO_TILT, 0);
        #else
            ledcWrite(0, 0);
            ledcWrite(1, 0);
        #endif
        return;
    }

    float effectivePan = INVERT_PAN ? (180.0f - pan) : pan;
    float effectiveTilt = INVERT_TILT ? (180.0f - tilt) : tilt;

    effectivePan = constrain(effectivePan, MIN_ANGLE, MAX_ANGLE);
    effectiveTilt = constrain(effectiveTilt, MIN_TILT_ANGLE, MAX_TILT_ANGLE); // Strict 60° to 120°

    // If Pan is centered inside deadband of 90°, cut its pulse to eliminate crawl
    if (abs(pan - 90.0f) < 0.5f) {
        pwm.setPin(CH_PAN, 0, false);
        #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
            ledcWrite(DIRECT_GPIO_PAN, 0);
        #else
            ledcWrite(0, 0);
        #endif
    } else {
        uint16_t pulsePan = angleToPcaPulse(effectivePan);
        pwm.setPWM(CH_PAN, 0, pulsePan);
        uint32_t dutyPan = angleToGpioDuty(effectivePan);
        #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
            ledcWrite(DIRECT_GPIO_PAN, dutyPan);
        #else
            ledcWrite(0, dutyPan);
        #endif
    }

    // Drive Tilt (Strict 60° to 120°)
    uint16_t pulseTilt = angleToPcaPulse(effectiveTilt);
    pwm.setPWM(CH_TILT, 0, pulseTilt);
    pwm.setPWM(CH_TILT_ALT, 0, pulseTilt);

    uint32_t dutyTilt = angleToGpioDuty(effectiveTilt);
    #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
        ledcWrite(DIRECT_GPIO_TILT, dutyTilt);
    #else
        ledcWrite(1, dutyTilt);
    #endif
}

void parseCommand(const String& line) {
    // Check if tracking is inactive / no target detected: Freeze both immediately
    if (line.indexOf("\"tracking\": false") >= 0 || line.indexOf("\"tracking\":false") >= 0 ||
        line.indexOf("\"stop\": true") >= 0 || line.indexOf("\"stop\":true") >= 0) {
        isTracking = false;
        lastCommandTime = millis();
        targetPan = 90.0f;
        targetTilt = 90.0f;
        currentPan = 90.0f;
        currentTilt = 90.0f;
        applyOutputs(90.0f, 90.0f, false);
        Serial.println("{\"servo_pan\": 90.0, \"servo_tilt\": 90.0, \"status\": \"STOPPED\"}");
        return;
    }

    bool hasPan = false, hasTilt = false;
    float newPan = targetPan, newTilt = targetTilt;

    if (line.startsWith("PAN:")) { newPan = line.substring(4).toFloat(); hasPan = true; }
    if (line.startsWith("TILT:")) { newTilt = line.substring(5).toFloat(); hasTilt = true; }

    int idxPan = line.indexOf("\"pan\":");
    if (idxPan >= 0) {
        idxPan += 6;
        while (idxPan < line.length() && (line[idxPan] == ' ' || line[idxPan] == ':')) idxPan++;
        newPan = line.substring(idxPan).toFloat();
        hasPan = true;
    }
    int idxTilt = line.indexOf("\"tilt\":");
    if (idxTilt >= 0) {
        idxTilt += 7;
        while (idxTilt < line.length() && (line[idxTilt] == ' ' || line[idxTilt] == ':')) idxTilt++;
        newTilt = line.substring(idxTilt).toFloat();
        hasTilt = true;
    }

    if (hasPan || hasTilt) {
        isTracking = true;
        lastCommandTime = millis();
        targetPan = constrain(newPan, MIN_ANGLE, MAX_ANGLE);
        targetTilt = constrain(newTilt, MIN_TILT_ANGLE, MAX_TILT_ANGLE); // Strictly 60° to 120°
        Serial.printf("{\"servo_pan\": %.1f, \"servo_tilt\": %.1f, \"status\": \"TRACKING\"}\n", currentPan, currentTilt);
    }
}

void setup() {
    Serial.begin(SERIAL_BAUD);
    pinMode(HEARTBEAT_LED, OUTPUT);

    Wire.begin(21, 22);
    Wire.setClock(400000); // 400kHz Fast I2C

    pwm.begin();
    pwm.setOscillatorFrequency(27000000);
    pwm.setPWMFreq(PWM_FREQ);

    #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
        ledcAttach(DIRECT_GPIO_PAN, PWM_FREQ, PWM_RESOLUTION);
        ledcAttach(DIRECT_GPIO_TILT, PWM_FREQ, PWM_RESOLUTION);
    #else
        ledcSetup(0, PWM_FREQ, PWM_RESOLUTION);
        ledcAttachPin(DIRECT_GPIO_PAN, 0);
        ledcSetup(1, PWM_FREQ, PWM_RESOLUTION);
        ledcAttachPin(DIRECT_GPIO_TILT, 1);
    #endif

    isTracking = false;
    currentPan = 90.0f;
    currentTilt = 90.0f;
    targetPan = 90.0f;
    targetTilt = 90.0f;
    lastCommandTime = millis();
    applyOutputs(90.0f, 90.0f, false);
    Serial.println("READY:DUAL_AXIS_CONTROLLED");
}

void loop() {
    // 1. Read Serial Command
    while (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') {
            rxBuffer.trim();
            if (rxBuffer.length() > 0) parseCommand(rxBuffer);
            rxBuffer = "";
        } else {
            rxBuffer += c;
        }
    }

    uint32_t now = millis();

    // 2. Slow, Smooth Speed Control (50 Hz Slew Rate Interpolation)
    if (now - lastSlewUpdate >= 20) {
        lastSlewUpdate = now;

        if (isTracking) {
            // Smooth slow Pan
            float diffPan = targetPan - currentPan;
            if (abs(diffPan) > 0.05f) {
                if (diffPan > 0) currentPan += (diffPan > MAX_PAN_STEP) ? MAX_PAN_STEP : diffPan;
                else currentPan -= (-diffPan > MAX_PAN_STEP) ? MAX_PAN_STEP : -diffPan;
            }

            // Smooth slow Tilt
            float diffTilt = targetTilt - currentTilt;
            if (abs(diffTilt) > 0.05f) {
                if (diffTilt > 0) currentTilt += (diffTilt > MAX_TILT_STEP) ? MAX_TILT_STEP : diffTilt;
                else currentTilt -= (-diffTilt > MAX_TILT_STEP) ? MAX_TILT_STEP : -diffTilt;
            }

            applyOutputs(currentPan, currentTilt, true);
        } else {
            // NOT tracking -> make sure motors are completely off
            applyOutputs(90.0f, 90.0f, false);
        }
    }

    // 3. Safety Watchdog: If no tracking command received for > 350ms, STOP ALL MOTORS!
    if (now - lastCommandTime > SAFETY_WATCHDOG_MS) {
        if (isTracking) {
            isTracking = false;
            targetPan = 90.0f;
            targetTilt = 90.0f;
            currentPan = 90.0f;
            currentTilt = 90.0f;
            applyOutputs(90.0f, 90.0f, false);
        }
    }

    // 4. Heartbeat LED Blink (every 500ms)
    if (now - lastHeartbeat >= 500) {
        lastHeartbeat = now;
        ledState = !ledState;
        digitalWrite(HEARTBEAT_LED, ledState ? HIGH : LOW);
    }
}
