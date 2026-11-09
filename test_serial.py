
import serial
import time

PORT = "COM6"
BAUD_RATE = 115200

try:
    arduino = serial.Serial(PORT, BAUD_RATE, timeout=1)

    print("SIGNAL DOCTOR")
    print("Arduino connected!")
    print("Receiving signal data...\n")

    time.sleep(2)
    arduino.reset_input_buffer()

    while True:
        line = arduino.readline().decode(
            "utf-8", errors="ignore"
        ).strip()

        if line:
            print(line)

except serial.SerialException as error:
    print("Connection error:", error)

except KeyboardInterrupt:
    print("\nConnection stopped.")

finally:
    if "arduino" in locals() and arduino.is_open:
        arduino.close()
