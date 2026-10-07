"""
VayuNetra — Manual Servo Test
==============================
Sends TILT:<angle> commands directly to the ESP32 on COM5.
Use this to verify the servo moves to the correct physical positions.

Expected Results:
    TILT:70  → servo turns LEFT
    TILT:80  → servo turns LEFT
    TILT:90  → servo at CENTER
    TILT:100 → servo turns RIGHT
    TILT:120 → servo turns RIGHT

Usage:
    python servo_tracker/manual_test.py
"""

import time
import serial

PORT = "COM5"
BAUD = 115200


def main():
    print(f"Opening {PORT} @ {BAUD}...")
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1.0)
    except Exception as e:
        print(f"ERROR: Cannot open {PORT}: {e}")
        print("Make sure:")
        print("  1. ESP32 is plugged in via USB")
        print("  2. No other program is using COM5 (close Arduino Serial Monitor)")
        print("  3. The esp32_tilt_receiver firmware is uploaded")
        return

    time.sleep(2.0)  # Wait for ESP32 boot

    # Read startup message
    while ser.in_waiting > 0:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        print(f"  [ESP32] {line}")

    print("\n" + "=" * 50)
    print("  VayuNetra Manual Servo Test")
    print("=" * 50)
    print("\nCommands:")
    print("  Type an angle (70-120) and press Enter")
    print("  Type 'sweep' to run a full sweep test")
    print("  Type 'q' to quit\n")

    while True:
        try:
            user = input("TILT> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if user.lower() == "q":
            break

        if user.lower() == "sweep":
            print("\n--- Sweep Test ---")
            for angle in [90, 70, 75, 80, 85, 90, 95, 100, 110, 120, 110, 100, 90]:
                cmd = f"TILT:{angle}\n"
                ser.write(cmd.encode("utf-8"))
                ser.flush()
                print(f"  Sent TILT:{angle}°", end="")

                time.sleep(0.5)
                while ser.in_waiting > 0:
                    resp = ser.readline().decode("utf-8", errors="ignore").strip()
                    print(f"  → ESP32: {resp}", end="")
                print()
                time.sleep(0.3)

            print("--- Sweep Complete ---\n")
            continue

        try:
            angle = float(user)
        except ValueError:
            print("  Invalid input. Enter a number (70-120) or 'sweep' or 'q'.")
            continue

        if angle < 0 or angle > 180:
            print("  WARNING: Angle out of 0-180 range!")

        cmd = f"TILT:{angle}\n"
        ser.write(cmd.encode("utf-8"))
        ser.flush()
        print(f"  Sent: TILT:{angle}")

        time.sleep(0.3)
        while ser.in_waiting > 0:
            resp = ser.readline().decode("utf-8", errors="ignore").strip()
            print(f"  [ESP32] {resp}")

    # Return to center before exit
    ser.write(b"TILT:90\n")
    ser.flush()
    time.sleep(0.5)
    ser.close()
    print("\nServo returned to 90° (center). Port closed.")


if __name__ == "__main__":
    main()
