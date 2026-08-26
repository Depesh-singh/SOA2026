/*
 * =====================================================================================
 * SMART-SHIELD v3.0: Microcontroller Firmware (ESP32)
 * AI-Powered Multi-Target Drone Detection, Tracking & Cyber-Defence Edge Controller
 * =====================================================================================
 * Pinout / Interfaces:
 * - LD2450 mmWave Radar: Serial2 (RX2: GPIO 16, TX2: GPIO 17 @ 256000 bps)
 * - PCA9685 16-Ch PWM Servo Driver: I2C (SDA: GPIO 21, SCL: GPIO 22, Addr: 0x40)
 * - SSD1306 128x64 OLED Display: I2C (SDA: GPIO 21, SCL: GPIO 22, Addr: 0x3C)
 * - WS2812B RGB Alert LEDs: GPIO 18 (8 LEDs NeoPixel Ring / Strip)
 * - Active Piezo Threat Buzzer: GPIO 19
 * - HC-SR04 Ultrasonic Sensor: Trig: GPIO 4, Echo: GPIO 5
 * - Battery Voltage Divider: ADC GPIO 34 (100k / 22k divider, 12V Li-ion monitor)
 * - AI Engine / Laptop CDC Link: Serial (USB @ 115200 bps)
 * =====================================================================================
 */

#include <Wire.h>
#include <ArduinoJson.h>
#include <Adafruit_PWMServoDriver.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_NeoPixel.h>

// ----------------- PIN DEFINITIONS -----------------
#define RADAR_RX_PIN        16
#define RADAR_TX_PIN        17
#define I2C_SDA_PIN         21
#define I2C_SCL_PIN         22
#define RGB_LED_PIN         18
#define BUZZER_PIN          19
#define ULTRASONIC_TRIG_PIN 4
#define ULTRASONIC_ECHO_PIN 5
#define BATTERY_ADC_PIN     34

#define NUM_LEDS            8
#define SCREEN_WIDTH        128
#define SCREEN_HEIGHT       64
#define OLED_RESET          -1

// PCA9685 Servo Channels & Pulse Lengths
#define SERVO_PAN_CH        0
#define SERVO_TILT_CH       1
#define SERVOMIN            150  // 0 degrees (~500us at 50Hz)
#define SERVOMAX            600  // 180 degrees (~2500us at 50Hz)

// ----------------- HARDWARE OBJECTS -----------------
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
Adafruit_NeoPixel strip(NUM_LEDS, RGB_LED_PIN, NEO_GRB + NEO_KHZ800);

// ----------------- SYSTEM STATE VARIABLES -----------------
struct RadarTarget {
  int16_t x_mm;
  int16_t y_mm;
  int16_t speed_cms;
  uint16_t snr_resolution;
  bool valid;
};

RadarTarget radarTargets[3];
float currentPanAngle = 90.0;
float currentTiltAngle = 45.0;
String currentThreatLevel = "LOW";
bool buzzerActive = false;
float batteryVoltage = 12.4;
float ultrasonicDistanceMeters = 0.0;
uint32_t lastTelemetryTime = 0;
uint32_t lastOledUpdateTime = 0;
uint32_t lastUltrasonicTime = 0;
uint32_t strobeTimer = 0;
bool strobeState = false;

// ----------------- HELPER FUNCTIONS -----------------

uint16_t angleToPwm(float angleDeg) {
  angleDeg = constrain(angleDeg, 0.0, 180.0);
  return map((int)(angleDeg * 10), 0, 1800, SERVOMIN, SERVOMAX);
}

void setGimbalServos(float pan, float tilt) {
  currentPanAngle = constrain(pan, 0.0, 180.0);
  currentTiltAngle = constrain(tilt, 15.0, 90.0);
  
  pwm.setPWM(SERVO_PAN_CH, 0, angleToPwm(currentPanAngle));
  pwm.setPWM(SERVO_TILT_CH, 0, angleToPwm(currentTiltAngle));
}

void updateLeds() {
  uint32_t now = millis();
  if (currentThreatLevel == "HIGH") {
    // Fast Red Strobe for Critical High Threat
    if (now - strobeTimer > 100) {
      strobeTimer = now;
      strobeState = !strobeState;
      uint32_t color = strobeState ? strip.Color(255, 0, 0) : strip.Color(0, 0, 0);
      for (int i = 0; i < NUM_LEDS; i++) strip.setPixelColor(i, color);
      strip.show();
    }
  } else if (currentThreatLevel == "MEDIUM") {
    // Steady Amber/Yellow for Elevated Threat
    for (int i = 0; i < NUM_LEDS; i++) strip.setPixelColor(i, strip.Color(255, 140, 0));
    strip.show();
  } else {
    // Calm Green Breathing Pulse for Nominal State
    uint8_t brightness = (sin(now / 400.0) + 1.0) * 40 + 10;
    for (int i = 0; i < NUM_LEDS; i++) strip.setPixelColor(i, strip.Color(0, brightness, 0));
    strip.show();
  }
}

void updateBuzzer() {
  if (buzzerActive || currentThreatLevel == "HIGH") {
    // Pulsed warning tone (2.4kHz)
    if ((millis() / 150) % 2 == 0) {
      digitalWrite(BUZZER_PIN, HIGH);
    } else {
      digitalWrite(BUZZER_PIN, LOW);
    }
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }
}

void readUltrasonicSensor() {
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  
  long duration = pulseIn(ULTRASONIC_ECHO_PIN, HIGH, 30000); // 30ms timeout
  if (duration > 0) {
    ultrasonicDistanceMeters = (duration * 0.0343) / 2.0 / 100.0; // in meters
  } else {
    ultrasonicDistanceMeters = 4.0; // Out of range
  }
}

void readBatteryVoltage() {
  int rawAdc = analogRead(BATTERY_ADC_PIN);
  // Divider: R1=100k, R2=22k -> Ratio = (100+22)/22 = 5.545
  // ESP32 ADC: 3.3V / 4095
  float pinVoltage = (rawAdc / 4095.0) * 3.3;
  batteryVoltage = pinVoltage * 5.545;
}

void updateOledDisplay() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  // Header
  display.setCursor(0, 0);
  display.print("SMART-SHIELD v3.0 C2");
  display.drawFastHLine(0, 10, SCREEN_WIDTH, SSD1306_WHITE);
  
  // System Status
  display.setCursor(0, 14);
  display.print("STATE: ARMED");
  display.setCursor(75, 14);
  display.print(batteryVoltage, 1);
  display.print("V");
  
  // Threat Level
  display.setCursor(0, 26);
  display.print("THREAT: ");
  display.print(currentThreatLevel);
  
  // Gimbal Coordinates
  display.setCursor(0, 38);
  display.print("PAN: ");
  display.print(currentPanAngle, 1);
  display.print((char)247);
  display.print(" TILT: ");
  display.print(currentTiltAngle, 1);
  display.print((char)247);
  
  // Radar & Proximity
  int activeCount = 0;
  for (int i = 0; i < 3; i++) if (radarTargets[i].valid) activeCount++;
  display.setCursor(0, 50);
  display.print("RADAR TRK: 0");
  display.print(activeCount);
  display.print(" PROX:");
  display.print(ultrasonicDistanceMeters, 1);
  display.print("m");
  
  display.display();
}

// ----------------- LD2450 RADAR PARSER -----------------

void parseRadarFrame() {
  // LD2450 Frame: Header 0xAA 0xFF 0x03 0x00 (4B) + 3 targets (8B each) + Tail 0x55 0xCC (2B) = 30 Bytes
  while (Serial2.available() >= 30) {
    if (Serial2.read() == 0xAA && Serial2.peek() == 0xFF) {
      uint8_t buffer[29];
      Serial2.readBytes(buffer, 29);
      
      if (buffer[0] == 0xFF && buffer[1] == 0x03 && buffer[2] == 0x00 &&
          buffer[27] == 0x55 && buffer[28] == 0xCC) {
        
        // Parse 3 target slots
        for (int i = 0; i < 3; i++) {
          int offset = 3 + i * 8;
          int16_t x = (int16_t)(buffer[offset] | (buffer[offset + 1] << 8));
          int16_t y = (int16_t)(buffer[offset + 2] | (buffer[offset + 3] << 8));
          int16_t speed = (int16_t)(buffer[offset + 4] | (buffer[offset + 5] << 8));
          uint16_t res = (uint16_t)(buffer[offset + 6] | (buffer[offset + 7] << 8));
          
          if (x != 0 || y != 0) {
            radarTargets[i].x_mm = x;
            radarTargets[i].y_mm = y;
            radarTargets[i].speed_cms = speed;
            radarTargets[i].snr_resolution = res;
            radarTargets[i].valid = true;
          } else {
            radarTargets[i].valid = false;
          }
        }
      }
    }
  }
}

// ----------------- JSON HOST COMMUNICATION -----------------

void sendTelemetryToHost() {
  StaticJsonDocument<512> doc;
  doc["timestamp"] = millis();
  doc["status"] = "ARMED";
  doc["battery_v"] = round(batteryVoltage * 10.0) / 10.0;
  doc["ultrasonic_m"] = round(ultrasonicDistanceMeters * 10.0) / 10.0;
  
  JsonObject gimbal = doc.createNestedObject("gimbal");
  gimbal["pan"] = currentPanAngle;
  gimbal["tilt"] = currentTiltAngle;
  
  JsonArray targetsArray = doc.createNestedArray("radar_targets");
  for (int i = 0; i < 3; i++) {
    if (radarTargets[i].valid) {
      JsonObject t = targetsArray.createNestedObject();
      t["slot"] = i + 1;
      t["x_mm"] = radarTargets[i].x_mm;
      t["y_mm"] = radarTargets[i].y_mm;
      t["speed_cms"] = radarTargets[i].speed_cms;
      t["snr"] = radarTargets[i].snr_resolution;
    }
  }
  
  serializeJson(doc, Serial);
  Serial.println();
}

void processIncomingHostCommands() {
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) return;
    
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, line);
    if (!error) {
      if (doc.containsKey("pan") && doc.containsKey("tilt")) {
        float p = doc["pan"];
        float t = doc["tilt"];
        setGimbalServos(p, t);
      }
      if (doc.containsKey("threat")) {
        currentThreatLevel = doc["threat"].as<String>();
      }
      if (doc.containsKey("buzzer")) {
        buzzerActive = doc["buzzer"].as<bool>();
      }
    }
  }
}

// ----------------- ARDUINO SETUP & LOOP -----------------

void setup() {
  // 1. USB Serial Link to Laptop AI Engine
  Serial.begin(115200);
  
  // 2. Hardware Serial2 for LD2450 mmWave Radar
  Serial2.begin(256000, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
  
  // 3. I2C Bus initialization
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  
  // 4. Initialize PCA9685 PWM Servo Driver
  pwm.begin();
  pwm.setPWMFreq(50); // 50Hz standard for servos
  setGimbalServos(90.0, 45.0); // Center positions
  
  // 5. Initialize SSD1306 OLED Display
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    display.clearDisplay();
    display.display();
  }
  
  // 6. Initialize WS2812B RGB LEDs
  strip.begin();
  strip.setBrightness(80);
  strip.show();
  
  // 7. GPIO Pin Modes
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);
  pinMode(BATTERY_ADC_PIN, INPUT);
  
  // Initial Display Splash
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(15, 20);
  display.println("SMART-SHIELD v3.0");
  display.setCursor(10, 35);
  display.println("SYSTEM INITIALIZED");
  display.display();
  delay(800);
}

void loop() {
  uint32_t now = millis();
  
  // 1. Process LD2450 Radar Packets
  parseRadarFrame();
  
  // 2. Process Host JSON Commands
  processIncomingHostCommands();
  
  // 3. Read Ultrasonic Distance Sensor (every 100ms)
  if (now - lastUltrasonicTime > 100) {
    lastUltrasonicTime = now;
    readUltrasonicSensor();
    readBatteryVoltage();
  }
  
  // 4. Update Indicators & Actuation
  updateLeds();
  updateBuzzer();
  
  // 5. Update Local OLED Display (10Hz)
  if (now - lastOledUpdateTime > 100) {
    lastOledUpdateTime = now;
    updateOledDisplay();
  }
  
  // 6. Transmit Telemetry Packet to AI Engine (20Hz)
  if (now - lastTelemetryTime > 50) {
    lastTelemetryTime = now;
    sendTelemetryToHost();
  }
}
